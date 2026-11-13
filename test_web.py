"""
Agente de Acessibilidade Educacional - IFPR.

Servidor de integração:
- Microfone físico.
- Microfone remoto pelo navegador.
- Vosk.
- Whisper.
- WebSocket de legendas.
- Controle das aulas.
- Gemini.
- PDF.
- E-mail.
"""

import asyncio
import json
import threading

from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

import uvicorn

from robo import config
from robo import config_audio

from robo.aula import Aula
from robo.comandos import Comandos
from robo.escuta import Escuta
from robo.microfone import Microfone
from robo.microfone_remoto import MicrofoneRemoto


# ==========================================
# CONFIGURAÇÕES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

INTERFACE = BASE_DIR / "interface"

HOST = config_audio.HOST

PORTA = config_audio.PORTA

IP_SERVIDOR = config_audio.IP_SERVIDOR

IPS_PROFESSORES = config_audio.IPS_PROFESSORES


# ==========================================
# COMPONENTES
# ==========================================

aula = Aula()

comandos = Comandos(aula)

escuta = Escuta()

clientes = set()

microfone = None

microfone_local = None

microfone_remoto = None

microfone_conectado = None

modo_microfone = config_audio.MICROFONE_MODO_PADRAO

estado_microfone = "parado"

mensagem_microfone = "Aguardando fonte de áudio."

legenda_parcial = ""

processando = False

encerrando = False

tarefa_material = None

ultimo_processamento = None

proximo_importante = False

registros_importantes = set()

disciplina_whisper = "geral"

lock_texto = asyncio.Lock()

lock_eventos = asyncio.Lock()

lock_microfone = asyncio.Lock()

metadados = {
    "titulo": "Aula de programação",
    "professor": "Professor",
    "disciplina": "Desenvolvimento de Software"
}


# ==========================================
# MODELOS DAS REQUISIÇÕES
# ==========================================

class EntradaTexto(BaseModel):

    texto: str


class EntradaAula(BaseModel):

    titulo: str = "Aula de programação"

    professor: str = "Professor"

    disciplina: str = "Desenvolvimento de Software"

    vocabulario: str = "geral"


# ==========================================
# AUTORIZAÇÃO DO PROFESSOR
# ==========================================

def verificar_professor(request: Request):

    if request.client is None:

        raise HTTPException(
            status_code=403,
            detail="Acesso não autorizado."
        )

    if request.client.host not in IPS_PROFESSORES:

        raise HTTPException(
            status_code=403,
            detail=(
                "Dispositivo não autorizado: "
                f"{request.client.host}"
            )
        )

    if request.method == "POST":

        origem = request.headers.get("origin")

        permitidas = (
            config_audio.obter_origens_permitidas()
        )

        if origem and origem not in permitidas:

            raise HTTPException(
                status_code=403,
                detail="Origem não autorizada."
            )


# ==========================================
# DADOS DA AULA
# ==========================================

def dados_aula():

    dados = deepcopy(
        aula.exportar()
    )

    for registro in dados.get("registros", []):

        registro["aula_id"] = dados.get("id")

        registro["importante"] = (
            registro.get("id")
            in registros_importantes
        )

    return dados


def aula_ativa():

    return dados_aula().get("estado") in {
        "conteudo",
        "atividade",
        "trabalho"
    }


# ==========================================
# STATUS DO MICROFONE
# ==========================================

def microfone_em_execucao(dispositivo):

    if dispositivo is None:
        return False

    thread = getattr(
        dispositivo,
        "thread",
        None
    )

    if thread is not None:

        return thread.is_alive()

    return bool(
        getattr(dispositivo, "ativo", False)
    )


# ==========================================
# STATUS GERAL
# ==========================================

def obter_status():

    dados = dados_aula()

    registros = dados.get(
        "registros",
        []
    )

    status_remoto = {}

    if microfone_remoto:

        status_remoto = (
            microfone_remoto.obter_status()
        )

    return {
        "aula": {
            "id": dados.get("id"),
            "titulo": dados.get("titulo"),
            "professor": dados.get("professor"),
            "disciplina": dados.get("disciplina"),
            "estado": dados.get(
                "estado",
                "aguardando"
            ),
            "inicio": dados.get("inicio"),
            "fim": dados.get("fim")
        },

        "registros": registros[-500:],

        "total_registros": len(registros),

        "alunos_conectados": len(clientes),

        "microfone": estado_microfone,

        "mensagem_microfone": mensagem_microfone,

        "modo_microfone": modo_microfone,

        "microfone_local_ativo": bool(
            microfone_local
            and microfone_local.ativo
        ),

        "microfone_remoto_ativo": bool(
            microfone_conectado is not None
            and microfone_remoto
            and microfone_remoto.ativo
        ),

        "audio_remoto": status_remoto,

        "legenda_parcial": legenda_parcial,

        "processando": processando,

        "processamento": ultimo_processamento,

        "proximo_importante": proximo_importante,

        "configuracao": metadados.copy(),

        "vocabulario": disciplina_whisper
    }


# ==========================================
# TRANSMITIR EVENTOS
# ==========================================

async def transmitir(evento, dados):

    mensagem = {
        "evento": evento,
        "dados": dados
    }

    async def enviar(cliente):

        try:

            await asyncio.wait_for(
                cliente.send_json(mensagem),
                timeout=3
            )

        except Exception:

            clientes.discard(cliente)

    async with lock_eventos:

        await asyncio.gather(
            *[
                enviar(cliente)
                for cliente in list(clientes)
            ]
        )


# ==========================================
# CONFIGURAR VOCABULÁRIO
# ==========================================

def configurar_vocabulario(dispositivo):

    if dispositivo is None:
        return

    definir = getattr(
        dispositivo,
        "definir_disciplina",
        None
    )

    if callable(definir):

        definir(disciplina_whisper)

        return

    whisper = getattr(
        dispositivo,
        "whisper",
        None
    )

    if whisper is not None:

        whisper.definir_disciplina(
            disciplina_whisper
        )


# ==========================================
# INICIAR AULA
# ==========================================

async def iniciar_aula():

    global proximo_importante
    global ultimo_processamento
    global legenda_parcial

    if processando:

        raise ValueError(
            "A aula anterior ainda está sendo processada."
        )

    if aula_ativa():

        raise ValueError(
            "Já existe uma aula em andamento."
        )

    configurar_vocabulario(microfone)

    aula.iniciar(
        titulo=metadados["titulo"],
        professor=metadados["professor"],
        disciplina=metadados["disciplina"]
    )

    registros_importantes.clear()

    proximo_importante = False

    ultimo_processamento = None

    legenda_parcial = ""

    escuta.ativar()

    dados = dados_aula()

    await transmitir(
        "aula_iniciada",
        dados
    )

    print(
        f"\n[AULA] Iniciada: {dados['titulo']}"
    )


# ==========================================
# ALTERAR ESTADO DA AULA
# ==========================================

async def alterar_estado(comando):

    if not aula_ativa():

        raise ValueError(
            "Nenhuma aula em andamento."
        )

    comandos.processar(comando)

    dados = dados_aula()

    await transmitir(
        "estado_alterado",
        {
            "estado": dados["estado"]
        }
    )

    print(
        f"[AULA] Estado: {dados['estado']}"
    )


# ==========================================
# MARCAR INFORMAÇÃO IMPORTANTE
# ==========================================

async def marcar_importante():

    global proximo_importante

    if not aula_ativa():

        raise ValueError(
            "Nenhuma aula em andamento."
        )

    proximo_importante = True

    await transmitir(
        "comando_executado",
        {
            "comando": "isso é importante",
            "mensagem": (
                "O próximo trecho será marcado "
                "como importante."
            )
        }
    )

    print(
        "[AULA] Próximo trecho importante."
    )


# ==========================================
# REGISTRAR LEGENDA
# ==========================================

async def registrar_legenda(texto):

    global proximo_importante
    global legenda_parcial

    if not aula_ativa():
        return

    texto = texto.strip()

    if not texto:
        return

    aula.registrar(texto)

    dados = dados_aula()

    registros = dados.get(
        "registros",
        []
    )

    if not registros:
        return

    registro = registros[-1]

    registro["aula_id"] = dados["id"]

    if proximo_importante:

        registros_importantes.add(
            registro["id"]
        )

        registro["importante"] = True

        proximo_importante = False

    legenda_parcial = ""

    await transmitir(
        "legenda",
        registro
    )

    if registro.get("importante"):

        await transmitir(
            "informacao_importante",
            registro
        )

    print(
        f"[LEGENDA] {texto}"
    )


# ==========================================
# LEGENDAS PARCIAIS
# ==========================================

async def processar_parcial(texto):

    global legenda_parcial

    if not aula_ativa():
        return

    legenda_parcial = texto

    await transmitir(
        "legenda_parcial",
        {
            "texto": texto,
            "aula_id": dados_aula().get("id")
        }
    )


# ==========================================
# SALVAR ARQUIVOS JSON
# ==========================================

def salvar_json(arquivo, dados):

    arquivo = Path(arquivo)

    arquivo.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporario = arquivo.with_suffix(
        ".json.tmp"
    )

    temporario.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )

    temporario.replace(arquivo)

    return arquivo


def salvar_transcricao(dados):

    arquivo = (
        Path(config.PASTA_TRANSCRICOES)
        / f"aula_{dados['id']}.json"
    )

    salvar_json(
        arquivo,
        dados
    )

    print(
        f"[ARQUIVO] Transcrição: {arquivo}"
    )

    return arquivo


def salvar_pendencia(dados, etapa, erro):

    arquivo = (
        Path(config.PASTA_PENDENCIAS)
        / f"processamento_{dados['id']}.json"
    )

    return salvar_json(
        arquivo,
        {
            "aula_id": dados["id"],
            "etapa": etapa,
            "erro": str(erro)
        }
    )


# ==========================================
# EVENTOS DO PROCESSAMENTO
# ==========================================

async def evento_processamento(
    evento,
    mensagem,
    dados=None
):

    global ultimo_processamento

    informacoes = {
        "mensagem": mensagem,
        **(dados or {})
    }

    ultimo_processamento = {
        "evento": evento,
        "dados": informacoes
    }

    await transmitir(
        evento,
        informacoes
    )


# ==========================================
# GEMINI + PDF + E-MAIL
# ==========================================

async def processar_material(dados):

    global processando

    etapa = "transcricao"

    try:

        arquivo_transcricao = (
            await asyncio.to_thread(
                salvar_transcricao,
                dados
            )
        )

        await evento_processamento(
            "transcricao_salva",
            "Transcrição salva com sucesso."
        )

        # Não utilizar o Gemini em aula vazia.
        if not dados.get("registros"):

            await evento_processamento(
                "erro_processamento",
                "A aula não possui conteúdo.",
                {
                    "etapa": "resumo"
                }
            )

            return

        etapa = "material"

        from robo.material import (
            ProcessadorMaterial
        )

        processador = ProcessadorMaterial()

        # ==================================
        # GEMINI
        # ==================================

        etapa = "resumo"

        await evento_processamento(
            "resumo_pendente",
            "Gerando resumo com Gemini..."
        )

        resultado = await asyncio.to_thread(
            processador.gerar_resumo,
            dados
        )

        if not isinstance(resultado, dict):

            raise RuntimeError(
                "Resposta inválida do resumidor."
            )

        if not resultado.get("sucesso"):

            raise RuntimeError(
                resultado.get("erro")
                or "Não foi possível gerar o resumo."
            )

        resumo = resultado.get("resumo")

        if not isinstance(resumo, dict):

            raise RuntimeError(
                "Resumo estruturado não encontrado."
            )

        await evento_processamento(
            "resumo_gerado",
            "Resumo gerado e validado.",
            {
                "tokens": resultado.get("tokens"),
                "tempo_processamento": resultado.get(
                    "tempo_processamento"
                )
            }
        )

        # ==================================
        # PDF
        # ==================================

        etapa = "pdf"

        arquivo_pdf = await asyncio.to_thread(
            processador.gerar_pdf,
            dados,
            resumo
        )

        arquivo_pdf = Path(arquivo_pdf)

        if not arquivo_pdf.is_file():

            raise RuntimeError(
                "O PDF não foi criado."
            )

        await evento_processamento(
            "pdf_gerado",
            "PDF gerado com sucesso.",
            {
                "arquivo": arquivo_pdf.name
            }
        )

        # ==================================
        # E-MAIL
        # ==================================

        if not getattr(
            config,
            "ENVIO_EMAIL_AUTOMATICO",
            True
        ):

            await evento_processamento(
                "processamento_concluido",
                "PDF gerado. Envio automático desativado."
            )

            return

        etapa = "email"

        resultado_email = await asyncio.to_thread(
            processador.enviar_email,
            dados,
            arquivo_pdf
        )

        if not isinstance(
            resultado_email,
            dict
        ):

            raise RuntimeError(
                "Resposta inválida do módulo de e-mail."
            )

        if (
            not resultado_email.get("sucesso")
            or resultado_email.get("falhas")
        ):

            raise RuntimeError(
                "O envio não foi concluído "
                "para todos os destinatários."
            )

        await evento_processamento(
            "email_enviado",
            "Material enviado por e-mail.",
            {
                "total": resultado_email.get(
                    "total",
                    0
                )
            }
        )

        print("\n" + "=" * 50)

        print(
            "[MATERIAL] Processamento concluído!"
        )

        print(
            f"Transcrição: {arquivo_transcricao}"
        )

        print(
            f"PDF: {arquivo_pdf}"
        )

        print("=" * 50)

    except Exception as erro:

        print(
            f"[ERRO] Etapa {etapa}: {erro}"
        )

        try:

            await asyncio.to_thread(
                salvar_pendencia,
                dados,
                etapa,
                erro
            )

        except Exception as erro_pendencia:

            print(
                f"[ERRO PENDÊNCIA] {erro_pendencia}"
            )

        await evento_processamento(
            "erro_processamento",
            f"Falha na etapa {etapa}. Consulte o terminal.",
            {
                "etapa": etapa
            }
        )

    finally:

        processando = False

        await transmitir(
            "status",
            obter_status()
        )


# ==========================================
# FINALIZAR AULA
# ==========================================

async def finalizar_aula():

    global processando
    global tarefa_material
    global proximo_importante
    global legenda_parcial

    if not aula_ativa():

        raise ValueError(
            "Nenhuma aula em andamento."
        )

    if processando:

        raise ValueError(
            "A aula já está sendo processada."
        )

    aula.finalizar()

    escuta.desativar()

    proximo_importante = False

    legenda_parcial = ""

    dados = dados_aula()

    processando = True

    await transmitir(
        "legenda_parcial",
        {
            "texto": "",
            "aula_id": dados["id"]
        }
    )

    await transmitir(
        "aula_finalizada",
        dados
    )

    tarefa_material = asyncio.create_task(
        processar_material(dados)
    )

    print(
        "[AULA] Finalizada."
    )

    print(
        "[AULA] Processando material..."
    )


# ==========================================
# PROCESSAR COMANDOS
# ==========================================

async def processar_texto(texto):

    texto = str(texto or "").strip()

    if not texto:
        return

    comando = escuta.identificar(texto)

    if comando == "iniciar aula":

        await iniciar_aula()

    elif comando in {
        "iniciar atividade",
        "iniciar trabalho",
        "continuar aula"
    }:

        await alterar_estado(comando)

    elif comando == "isso é importante":

        await marcar_importante()

    elif comando == "finalizar aula":

        await finalizar_aula()

    else:

        if not aula_ativa():

            raise ValueError(
                "Inicie uma aula primeiro."
            )

        await registrar_legenda(texto)


async def processar_manual(texto):

    async with lock_texto:

        await processar_texto(texto)


async def processar_voz(texto):

    async with lock_texto:

        resultado = escuta.processar(texto)

        if resultado is None:
            return

        try:

            await processar_texto(
                resultado["texto"]
            )

        except ValueError as erro:

            print(
                f"[COMANDO] {erro}"
            )

            await transmitir(
                "comando_rejeitado",
                {
                    "mensagem": str(erro)
                }
            )


# ==========================================
# ATUALIZAR STATUS DO MICROFONE
# ==========================================

async def atualizar_microfone(
    modo,
    estado,
    mensagem
):

    global estado_microfone
    global mensagem_microfone

    if modo != modo_microfone:
        return

    estado_microfone = estado

    mensagem_microfone = mensagem

    await transmitir(
        "microfone_status",
        {
            "estado": estado,
            "mensagem": mensagem,
            "modo": modo
        }
    )


# ==========================================
# PARAR UM DISPOSITIVO
# ==========================================

async def parar_dispositivo(dispositivo):

    if dispositivo is None:
        return True

    dispositivo.parar()

    resultado = await asyncio.to_thread(
        dispositivo.aguardar,
        config_audio.AUDIO_TIMEOUT_ENCERRAMENTO
    )

    if resultado is False:
        return False

    return not microfone_em_execucao(
        dispositivo
    )


# ==========================================
# SELECIONAR MICROFONE
# ==========================================

async def selecionar_microfone(modo):

    global microfone
    global modo_microfone

    if modo not in ("local", "remoto"):

        raise ValueError(
            "Fonte de áudio inválida."
        )

    if modo == "local":

        if not config_audio.MICROFONE_LOCAL_ATIVADO:

            raise ValueError(
                "Microfone físico desativado."
            )

        dispositivo = microfone_local

    else:

        if not config_audio.MICROFONE_REMOTO_ATIVADO:

            raise ValueError(
                "Microfone remoto desativado."
            )

        dispositivo = microfone_remoto

    if dispositivo is None:

        raise ValueError(
            "Microfone indisponível."
        )

    # Não misturar áudio de duas fontes.
    if (
        aula_ativa()
        and modo != modo_microfone
    ):

        raise ValueError(
            "Finalize a aula antes de trocar "
            "a fonte de áudio."
        )

    if (
        modo == "local"
        and microfone_conectado is not None
    ):

        raise ValueError(
            "Desconecte primeiro o celular."
        )

    if (
        microfone is not None
        and microfone is not dispositivo
        and microfone_em_execucao(microfone)
    ):

        raise ValueError(
            "Desative primeiro o microfone atual."
        )

    microfone = dispositivo

    modo_microfone = modo

    configurar_vocabulario(dispositivo)

    print(
        f"[ÁUDIO] Fonte selecionada: {modo}"
    )

    await transmitir(
        "microfone_modo",
        {
            "modo": modo
        }
    )

    return dispositivo


# ==========================================
# TERMINAL DO PROFESSOR
# ==========================================

def terminal_professor(loop):

    print("\n" + "=" * 50)

    print("AGENTE IHC - PROFESSOR")

    print("=" * 50)

    print(
        "\nComandos disponíveis:\n"
        "  iniciar aula\n"
        "  iniciar atividade\n"
        "  iniciar trabalho\n"
        "  continuar aula\n"
        "  isso é importante\n"
        "  finalizar aula\n"
    )

    while not encerrando:

        try:

            texto = input(
                "\nProfessor > "
            )

        except (
            EOFError,
            KeyboardInterrupt
        ):

            break

        if not texto.strip():
            continue

        if encerrando:
            break

        try:

            tarefa = (
                asyncio.run_coroutine_threadsafe(
                    processar_manual(texto),
                    loop
                )
            )

            tarefa.result()

        except Exception as erro:

            print(
                f"[ERRO TERMINAL] {erro}"
            )


# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================

@asynccontextmanager
async def lifespan(app):

    global microfone
    global microfone_local
    global microfone_remoto
    global modo_microfone
    global encerrando

    encerrando = False

    for diretorio in (
        config.PASTA_TRANSCRICOES,
        config.PASTA_RELATORIOS,
        config.PASTA_RESUMOS,
        config.PASTA_PENDENCIAS
    ):

        Path(diretorio).mkdir(
            parents=True,
            exist_ok=True
        )

    loop = asyncio.get_running_loop()

    # ======================================
    # CALLBACKS IDENTIFICADOS POR FONTE
    # ======================================

    def criar_callbacks(modo):

        def ao_texto(texto):

            if encerrando:
                return

            if modo != modo_microfone:
                return

            tarefa = (
                asyncio.run_coroutine_threadsafe(
                    processar_voz(texto),
                    loop
                )
            )

            try:

                tarefa.result()

            except Exception as erro:

                print(
                    f"[ERRO VOZ] {erro}"
                )

        def ao_parcial(texto):

            if encerrando:
                return

            if modo != modo_microfone:
                return

            asyncio.run_coroutine_threadsafe(
                processar_parcial(texto),
                loop
            )

        def ao_status(estado, mensagem):

            if encerrando:
                return

            asyncio.run_coroutine_threadsafe(
                atualizar_microfone(
                    modo,
                    estado,
                    mensagem
                ),
                loop
            )

        return {
            "ao_texto": ao_texto,
            "ao_parcial": ao_parcial,
            "ao_status": ao_status,
            "esta_registrando": (
                lambda: (
                    escuta.registrando
                    and modo == modo_microfone
                )
            )
        }

    # ======================================
    # MICROFONE FÍSICO
    # ======================================

    microfone_local = Microfone(
        **criar_callbacks("local")
    )

    # ======================================
    # MICROFONE REMOTO
    # ======================================

    microfone_remoto = MicrofoneRemoto(
        **criar_callbacks("remoto")
    )

    # ======================================
    # ESCOLHER MODO INICIAL
    # ======================================

    modo_microfone = (
        config_audio.MICROFONE_MODO_PADRAO
    )

    if modo_microfone == "local":

        microfone = microfone_local

        if (
            config_audio.MICROFONE_LOCAL_ATIVADO
            and config_audio.ESCUTA_LOCAL_AUTOMATICA
        ):

            microfone_local.iniciar()

    else:

        modo_microfone = "remoto"

        microfone = microfone_remoto

        print(
            "[ÁUDIO] Aguardando microfone do celular."
        )

    # ======================================
    # TERMINAL
    # ======================================

    terminal = threading.Thread(
        target=terminal_professor,
        args=(loop,),
        daemon=True
    )

    terminal.start()

    try:

        yield

    finally:

        encerrando = True

        escuta.desativar()

        for dispositivo in (
            microfone_local,
            microfone_remoto
        ):

            if dispositivo:

                await parar_dispositivo(
                    dispositivo
                )

        if (
            tarefa_material
            and not tarefa_material.done()
        ):

            print(
                "[SERVIDOR] Aguardando processamento."
            )

            await tarefa_material


# ==========================================
# APLICAÇÃO FASTAPI
# ==========================================

app = FastAPI(
    title="Agente IHC",
    lifespan=lifespan
)


# ==========================================
# WEBSOCKET DOS ALUNOS
# ==========================================

@app.websocket("/ws")
async def websocket_aluno(
    websocket: WebSocket
):

    await websocket.accept()

    try:

        async with lock_eventos:

            clientes.add(websocket)

            await websocket.send_json(
                {
                    "evento": "status",
                    "dados": obter_status()
                }
            )

            if ultimo_processamento:

                await websocket.send_json(
                    ultimo_processamento
                )

        print(
            f"[WEB] Cliente conectado. "
            f"Total: {len(clientes)}"
        )

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        pass

    finally:

        clientes.discard(websocket)

        print(
            f"[WEB] Cliente desconectado. "
            f"Total: {len(clientes)}"
        )


# ==========================================
# API - STATUS
# ==========================================

@app.get("/api/professor/status")
async def professor_status(
    request: Request
):

    verificar_professor(request)

    return obter_status()


# ==========================================
# API - CONFIGURAÇÃO DA AULA
# ==========================================

@app.post("/api/professor/configurar")
async def professor_configurar(
    request: Request,
    entrada: EntradaAula
):

    global disciplina_whisper

    verificar_professor(request)

    async with lock_texto:

        if aula_ativa() or processando:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Existe uma aula em andamento "
                    "ou em processamento."
                )
            )

        metadados.update(
            {
                "titulo": (
                    entrada.titulo.strip()
                    or "Aula de programação"
                ),

                "professor": (
                    entrada.professor.strip()
                    or "Professor"
                ),

                "disciplina": (
                    entrada.disciplina.strip()
                    or "Desenvolvimento de Software"
                )
            }
        )

        vocabularios = getattr(
            config,
            "VOCABULARIOS_DISCIPLINAS",
            {}
        )

        disciplina_whisper = (
            entrada.vocabulario
            if entrada.vocabulario in vocabularios
            else "geral"
        )

        configurar_vocabulario(
            microfone
        )

        return {
            "sucesso": True,
            "configuracao": metadados.copy(),
            "vocabulario": disciplina_whisper
        }


# ==========================================
# API - TEXTO MANUAL
# ==========================================

@app.post("/api/professor/texto")
async def professor_texto(
    request: Request,
    entrada: EntradaTexto
):

    verificar_professor(request)

    try:

        await processar_manual(
            entrada.texto
        )

    except ValueError as erro:

        raise HTTPException(
            status_code=409,
            detail=str(erro)
        )

    return {
        "sucesso": True,
        "status": obter_status()
    }


# ==========================================
# API - INICIAR MICROFONE FÍSICO
# ==========================================

@app.post("/api/professor/microfone/iniciar")
async def professor_microfone_iniciar(
    request: Request
):

    verificar_professor(request)

    async with lock_microfone:

        try:

            dispositivo = (
                await selecionar_microfone(
                    "local"
                )
            )

            if not dispositivo.ativo:

                if microfone_em_execucao(
                    dispositivo
                ):

                    raise ValueError(
                        "O microfone ainda está encerrando."
                    )

                dispositivo.iniciar()

        except ValueError as erro:

            raise HTTPException(
                status_code=409,
                detail=str(erro)
            )

        except Exception as erro:

            raise HTTPException(
                status_code=500,
                detail=str(erro)
            )

    return {
        "sucesso": True,
        "modo": "local",
        "status": obter_status()
    }


# ==========================================
# API - PARAR MICROFONE FÍSICO
# ==========================================

@app.post("/api/professor/microfone/parar")
async def professor_microfone_parar(
    request: Request
):

    verificar_professor(request)

    async with lock_microfone:

        terminou = await parar_dispositivo(
            microfone_local
        )

        if not terminou:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Microfone físico ainda está "
                    "encerrando o processamento."
                )
            )

    return {
        "sucesso": True,
        "modo": "local"
    }


# ==========================================
# WEBSOCKET - MICROFONE REMOTO
# ==========================================

@app.websocket(config_audio.ROTA_AUDIO)
async def websocket_microfone(
    websocket: WebSocket
):

    global microfone_conectado

    # ======================================
    # AUTORIZAÇÃO
    # ======================================

    if (
        websocket.client is None
        or websocket.client.host
        not in IPS_PROFESSORES
    ):

        await websocket.close(
            code=1008
        )

        return

    origem = websocket.headers.get(
        "origin"
    )

    if (
        origem
        not in config_audio.obter_origens_permitidas()
    ):

        await websocket.close(
            code=1008
        )

        return

    if (
        config_audio.EXIGIR_HTTPS_REMOTO
        and not origem.startswith("https://")
    ):

        await websocket.close(
            code=1008
        )

        return

    dispositivo = None

    # ======================================
    # SELECIONAR MICROFONE
    # ======================================

    async with lock_microfone:

        if microfone_conectado is not None:

            await websocket.close(
                code=1008
            )

            return

        try:

            dispositivo = (
                await selecionar_microfone(
                    "remoto"
                )
            )

        except ValueError as erro:

            print(
                f"[ÁUDIO] {erro}"
            )

            await websocket.close(
                code=1008
            )

            return

        if microfone_em_execucao(
            dispositivo
        ):

            await websocket.close(
                code=1013
            )

            return

        await websocket.accept()

        microfone_conectado = websocket

    # ======================================
    # CARREGAR MODELOS
    # ======================================

    try:

        iniciou = dispositivo.iniciar()

        if not iniciou:

            raise RuntimeError(
                "Não foi possível iniciar "
                "o microfone remoto."
            )

        await websocket.send_json(
            {
                "evento": "carregando",
                "mensagem": (
                    "Inicializando Vosk e Whisper..."
                )
            }
        )

        # Aguarda os modelos antes de receber
        # os blocos PCM do navegador.

        prazo = (
            asyncio.get_running_loop().time()
            + config_audio.AUDIO_TIMEOUT_MODELO
        )

        while not dispositivo.pronto.is_set():

            if dispositivo.erro_inicializacao:

                raise RuntimeError(
                    dispositivo.erro_inicializacao
                )

            if not dispositivo.ativo:

                raise RuntimeError(
                    "Microfone remoto foi encerrado."
                )

            if (
                asyncio.get_running_loop().time()
                >= prazo
            ):

                raise RuntimeError(
                    "Tempo limite para carregar modelos."
                )

            await asyncio.sleep(0.1)

        await websocket.send_json(
            {
                "evento": "pronto",
                "mensagem": (
                    "Microfone do celular conectado."
                )
            }
        )

        print(
            "[ÁUDIO] Celular conectado: "
            f"{websocket.client.host}"
        )

        # ==================================
        # RECEBER ÁUDIO
        # ==================================

        while True:

            try:

                mensagem = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=5
                )

            except asyncio.TimeoutError:

                if not dispositivo.ativo:

                    raise RuntimeError(
                        dispositivo.erro_inicializacao
                        or "Reconhecimento encerrado."
                    )

                continue

            if (
                mensagem["type"]
                == "websocket.disconnect"
            ):

                break

            audio = mensagem.get(
                "bytes"
            )

            if audio is None:

                continue

            if not dispositivo.receber_audio(
                audio
            ):

                raise RuntimeError(
                    "Não foi possível receber "
                    "o bloco de áudio."
                )

    except WebSocketDisconnect:

        print(
            "[ÁUDIO] Celular desconectado."
        )

    except Exception as erro:

        print(
            f"[ERRO ÁUDIO] {erro}"
        )

        try:

            await websocket.send_json(
                {
                    "evento": "erro",
                    "mensagem": str(erro)
                }
            )

            await websocket.close(
                code=1011
            )

        except Exception:

            pass

    finally:

        async with lock_microfone:

            if dispositivo:

                terminou = (
                    await parar_dispositivo(
                        dispositivo
                    )
                )

                if not terminou:

                    print(
                        "[ÁUDIO] Reconhecimento ainda "
                        "está encerrando."
                    )

            if microfone_conectado is websocket:

                microfone_conectado = None

        await transmitir(
            "status",
            obter_status()
        )


# ==========================================
# PÁGINA DO PROFESSOR
# ==========================================

@app.get("/professor")
@app.get("/professor.html")
async def pagina_professor(
    request: Request
):

    verificar_professor(request)

    return FileResponse(
        INTERFACE / "professor.html",
        media_type="text/html"
    )


# ==========================================
# FAVICON
# ==========================================

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():

    from fastapi.responses import Response

    return Response(
        status_code=204
    )


# ==========================================
# ARQUIVOS ESTÁTICOS
# ==========================================

# A montagem deve ser sempre a última rota.

app.mount(
    "/",
    StaticFiles(
        directory=str(INTERFACE),
        html=True
    ),
    name="interface"
)


# ==========================================
# EXECUTAR SERVIDOR
# ==========================================

if __name__ == "__main__":

    ssl_config = {}

    protocolo = "http"

    if config_audio.possui_certificados():

        protocolo = "https"

        ssl_config = {
            "ssl_certfile": str(
                config_audio.CERTIFICADO_SERVIDOR
            ),

            "ssl_keyfile": str(
                config_audio.CHAVE_SERVIDOR
            )
        }

    else:

        print(
            "[AVISO] Certificados HTTPS não encontrados."
        )

        print(
            "[AVISO] O microfone remoto ficará "
            "indisponível até configurar HTTPS."
        )

    print("\n" + "=" * 60)

    print("AGENTE IHC - SERVIDOR")

    print("=" * 60)

    print(
        f"\nAluno: "
        f"{protocolo}://{IP_SERVIDOR}:{PORTA}"
    )

    print(
        f"Professor: "
        f"{protocolo}://{IP_SERVIDOR}:{PORTA}/professor"
    )

    print(
        f"Professor local: "
        f"{protocolo}://localhost:{PORTA}/professor"
    )

    print(
        f"Microfone padrão: "
        f"{config_audio.MICROFONE_MODO_PADRAO}"
    )

    print(
        "\nIniciando servidor...\n"
    )

    uvicorn.run(
        app,
        host=HOST,
        port=PORTA,
        proxy_headers=False,
        ws_max_size=65536,
        **ssl_config
    )