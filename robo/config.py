"""
Configurações do Agente de Acessibilidade Educacional.

Projeto IHC - IFPR.
Baseado no Robô Byte para TV Box B13.

Reconhecimento:
- Vosk para comandos e legendas parciais.
- Whisper.cpp para transcrições definitivas.

Material:
- Gemini para organização do conteúdo.
- PDF para material de estudo.
- SMTP para envio por e-mail.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ==========================================
# DIRETÓRIO PRINCIPAL
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ==========================================
# DIRETÓRIOS DO PROJETO
# ==========================================

PASTA_DADOS = BASE_DIR / "dados"

PASTA_TRANSCRICOES = PASTA_DADOS / "transcricoes"

PASTA_RELATORIOS = PASTA_DADOS / "relatorios"

PASTA_RESUMOS = PASTA_DADOS / "resumos"

PASTA_PENDENCIAS = PASTA_DADOS / "pendencias"

PASTA_MODELOS = BASE_DIR / "modelos"

PASTA_INTERFACE = BASE_DIR / "interface"

PASTA_FERRAMENTAS = BASE_DIR / "ferramentas"

PASTA_CERTIFICADOS = BASE_DIR / "certificados"

PASTA_ROBO = BASE_DIR / "robo"


# ==========================================
# IDENTIDADE
# ==========================================

NOME_DO_ROBO = "Agente IHC"

IDIOMA = "pt-BR"

PALAVRAS_DE_ATIVACAO = [
    "ei robô",
    "eu robô",
    "oi robô",
    "olá robô",
    "byte",
    "oi byte"
]


# ==========================================
# COMANDOS PRINCIPAIS DA AULA
# ==========================================

COMANDO_INICIO = "iniciar aula"

COMANDO_ATIVIDADE = "iniciar atividade"

COMANDO_TRABALHO = "iniciar trabalho"

COMANDO_CONTINUAR = "continuar aula"

COMANDO_IMPORTANTE = "isso é importante"

COMANDO_FINAL = "finalizar aula"


# ==========================================
# APELIDOS DOS COMANDOS
# ==========================================

# Utilizado pelo robo/escuta.py.
# Não remover esta configuração.

APELIDOS_COMANDOS = {

    COMANDO_INICIO: [
        "iniciar aula",
        "iniciar a aula",
        "começar aula",
        "começar a aula",
        "início da aula",
        "começar a registrar"
    ],

    COMANDO_ATIVIDADE: [
        "iniciar atividade",
        "iniciar a atividade",
        "começar atividade",
        "começar a atividade",
        "início da atividade"
    ],

    COMANDO_TRABALHO: [
        "iniciar trabalho",
        "iniciar o trabalho",
        "começar trabalho",
        "começar o trabalho",
        "início do trabalho"
    ],

    COMANDO_CONTINUAR: [
        "continuar aula",
        "continuar a aula",
        "retomar aula",
        "retomar a aula",
        "voltar para a aula",
        "voltar ao conteúdo"
    ],

    COMANDO_IMPORTANTE: [
        "isso é importante",
        "isto é importante",
        "informação importante",
        "marcar como importante",
        "anotar isso",
        "prestem atenção"
    ],

    COMANDO_FINAL: [
        "finalizar aula",
        "finalizar a aula",
        "encerrar aula",
        "encerrar a aula",
        "terminar aula",
        "terminar a aula",
        "fim da aula"
    ]

}


# ==========================================
# MODELO VOSK
# ==========================================

MODELO_VOSK = (
    PASTA_MODELOS
    / "vosk-model-small-pt-0.3"
)

VOSK_TAXA_AMOSTRAGEM = 16000

VOSK_DISPOSITIVO = None

VOSK_TAMANHO_BLOCO = 4000

VOSK_TAMANHO_FILA = 120

VOSK_RESULTADOS_PARCIAIS = True

VOSK_NIVEL_LOG = -1

VOSK_VOCABULARIO_ATIVACAO = [
    *APELIDOS_COMANDOS[COMANDO_INICIO],
    "[unk]"
]

VOSK_VOCABULARIO_COMANDOS = list(
    dict.fromkeys(
        [
            apelido
            for apelidos in APELIDOS_COMANDOS.values()
            for apelido in apelidos
        ]
        + ["[unk]"]
    )
)


# ==========================================
# CONFIGURAÇÕES DE ÁUDIO
# ==========================================

TAXA_DE_AMOSTRAGEM = VOSK_TAXA_AMOSTRAGEM

DISPOSITIVO_MICROFONE = VOSK_DISPOSITIVO

LIMIAR_DE_SILENCIO = 600

SEGUNDOS_DE_SILENCIO_PARA_PARAR = 1

SEGUNDOS_MAXIMOS_DE_FALA = 25

SEGUNDOS_ESPERANDO_PERGUNTA = 4

ESCUTA_AUTOMATICA = True


# ==========================================
# MOTOR DE RECONHECIMENTO
# ==========================================

MOTOR_ENTENDIMENTO = "whisper"

SO_OFFLINE = True

NUCLEOS_DO_PROCESSADOR = 4


# ==========================================
# PARAKEET - COMPATIBILIDADE ORIGINAL
# ==========================================

PASTA_PARAKEET = str(
    PASTA_MODELOS / "parakeet-ptBR"
)

PARAKEET_QUANTIZACAO = "int8"


# ==========================================
# WHISPER.CPP
# ==========================================

# Modelo original, mantido por compatibilidade.

MODELO_WHISPER = "base"

PASTA_WHISPER = PASTA_MODELOS / "whisper"

# Modelo efetivamente utilizado pelo whisper.cpp.

ARQUIVO_MODELO_WHISPER = (
    PASTA_WHISPER
    / "ggml-base-q5_1.bin"
)

# Executável compilado anteriormente.

WHISPER_EXECUTAVEL = (
    PASTA_FERRAMENTAS
    / "whisper.cpp"
    / "build"
    / "bin"
    / "whisper-cli"
)

# Português como idioma predominante,
# mantendo termos técnicos em inglês.

WHISPER_IDIOMA = "pt"

WHISPER_THREADS = 2

WHISPER_MAX_SEGUNDOS = 12

WHISPER_TIMEOUT = 120

WHISPER_TRADUZIR = False

WHISPER_SEM_TIMESTAMPS = True

WHISPER_FALLBACK_VOSK = True

CAPRICHO_DO_WHISPER = 3

DICA_WHISPER = (
    "Aula acadêmica de programação em português "
    "brasileiro, com termos técnicos em inglês. "
    "Professor explicando conceitos, códigos, "
    "atividades e trabalhos."
)


# ==========================================
# VOCABULÁRIO TÉCNICO GERAL
# ==========================================

VOCABULARIO_TECNICO = """
Aula de programação e desenvolvimento de software.

Java, Python, JavaScript, TypeScript, PHP,
C, C++, C Sharp, C#, Kotlin, Ruby, Rust, Go.

Spring Boot, Spring Security, Hibernate, JPA,
Thymeleaf, Maven, Gradle, Vue.js, React, Angular,
Node.js, Vite, Express, Laravel, Slim Framework.

HTML, CSS, Bootstrap, Tailwind CSS.

MySQL, PostgreSQL, SQLite, MongoDB, Redis,
SQL, SELECT, INSERT, UPDATE, DELETE,
INNER JOIN, LEFT JOIN, RIGHT JOIN,
foreign key, primary key, constraint,
index, database, schema, transaction.

Git, GitHub, GitLab, Docker, Kubernetes,
Linux, Ubuntu, Debian, Bash, terminal.

API REST, RESTful, JSON, XML, HTTP, HTTPS,
WebSocket, endpoint, request, response,
JWT, token, authentication, authorization,
access token, refresh token.

Controller, Service, Repository, Entity,
DTO, Model, View, MVC, Clean Architecture.

Array, String, Boolean, Integer, Float,
Double, List, Map, Set, HashMap.

Class, Interface, Abstract, Extends,
Implements, Public, Private, Protected,
Static, Void, Return, Constructor,
Getter, Setter, Override, Overload.

If, Else, Switch, Case, For, While,
Try, Catch, Exception, Throw, Finally.

Frontend, Backend, Full Stack, Framework,
Library, Component, Router, Middleware,
Hook, State, Props, Event, Callback.

Commit, Push, Pull, Merge, Branch,
Pull Request, Clone, Checkout.

Scrum, Kanban, Sprint, Product Owner,
Backlog, Design Pattern, Singleton,
Factory, Observer, Dependency Injection.

Inteligência artificial, Machine Learning,
Deep Learning, Prompt, LLM, Gemini,
Whisper, Vosk, Speech Recognition.

FastAPI, Uvicorn, WebSocket, Pydantic,
Python, Asyncio, Thread, Queue.

Acessibilidade, interação humano-computador,
usabilidade, experiência do usuário,
interface, legenda, transcrição.
"""


# ==========================================
# VOCABULÁRIOS POR DISCIPLINA
# ==========================================

VOCABULARIOS_DISCIPLINAS = {

    "geral": (
        "Java, Python, JavaScript, TypeScript, PHP, "
        "C++, SQL, Git, GitHub, algoritmo, função, "
        "classe, variável, método, array, objeto."
    ),

    "banco_de_dados": (
        "SQL, MySQL, PostgreSQL, SELECT, INSERT, "
        "UPDATE, DELETE, INNER JOIN, LEFT JOIN, "
        "RIGHT JOIN, GROUP BY, ORDER BY, HAVING, "
        "primary key, foreign key, constraint, "
        "index, schema, transaction, commit, rollback, "
        "normalização, entidade, relacionamento."
    ),

    "desenvolvimento_web": (
        "Java, Spring Boot, Spring MVC, Hibernate, "
        "JPA, Thymeleaf, Controller, Service, Repository, "
        "Entity, DTO, API REST, JSON, HTTP, HTTPS, "
        "GET, POST, PUT, PATCH, DELETE, endpoint, "
        "request, response, Maven, Gradle, "
        "HTML, CSS, JavaScript, TypeScript."
    ),

    "vue": (
        "Vue.js, Vue Router, Vite, TypeScript, "
        "JavaScript, Composition API, Options API, "
        "ref, reactive, computed, watch, onMounted, "
        "component, props, emit, template, script, "
        "style, v-if, v-for, v-model, v-bind, "
        "v-on, RouterLink, RouterView, npm, Node.js."
    ),

    "orientacao_objetos": (
        "Java, class, object, interface, abstract, "
        "extends, implements, public, private, "
        "protected, static, final, constructor, "
        "getter, setter, override, overload, "
        "encapsulamento, herança, polimorfismo, "
        "abstração, composição, associação, SOLID."
    ),

    "redes": (
        "TCP, UDP, IP, IPv4, IPv6, DNS, DHCP, "
        "HTTP, HTTPS, SSH, FTP, SMTP, WebSocket, "
        "socket, gateway, router, switch, "
        "subnet, máscara de rede, firewall, "
        "modelo OSI, camada de transporte, "
        "endereço MAC, Ethernet."
    ),

    "sistemas_operacionais": (
        "Linux, Ubuntu, Debian, kernel, shell, "
        "Bash, process, thread, mutex, semaphore, "
        "deadlock, scheduling, CPU, RAM, cache, "
        "memória virtual, paginação, sistema de arquivos, "
        "escalonamento, concorrência, paralelismo."
    ),

    "inteligencia_artificial": (
        "Inteligência artificial, Machine Learning, "
        "Deep Learning, neural network, transformer, "
        "LLM, Gemini, GPT, Whisper, Vosk, prompt, "
        "token, embedding, inference, training, "
        "dataset, model, fine-tuning, RAG, "
        "speech recognition, natural language processing."
    ),

    "engenharia_software": (
        "Scrum, Kanban, Sprint, Product Owner, "
        "Scrum Master, backlog, user story, "
        "requisitos funcionais, requisitos não funcionais, "
        "design pattern, singleton, factory, observer, "
        "dependency injection, SOLID, UML, "
        "Clean Architecture, teste unitário, integração."
    ),

    "ihc": (
        "Interação humano-computador, IHC, "
        "acessibilidade, usabilidade, interface, "
        "experiência do usuário, UX, UI, "
        "design responsivo, leitor de tela, "
        "legenda em tempo real, transcrição, "
        "contraste, WCAG, feedback, protótipo, "
        "heurísticas de Nielsen, avaliação de interface."
    )

}


def obter_vocabulario(disciplina=None):
    """
    Retorna um contexto técnico curto para o Whisper.

    O vocabulário não deve funcionar como uma
    instrução para inventar palavras, apenas como
    contexto da disciplina.
    """

    disciplina = str(
        disciplina or "geral"
    ).strip().lower()

    vocabulario = VOCABULARIOS_DISCIPLINAS.get(
        disciplina,
        VOCABULARIOS_DISCIPLINAS["geral"]
    )

    return f"{DICA_WHISPER} {vocabulario}"


# ==========================================
# CÉREBRO ORIGINAL DO ROBÔ
# ==========================================

CEREBRO = "web"

MODELO_IA = "qwen2.5:0.5b"

MODELO_IA_OPCOES = {
    "temperature": 0.1,
    "repeat_penalty": 1.2,
    "num_ctx": 4096
}

TROCAS_NA_MEMORIA = 6

TAMANHO_MAXIMO_DA_RESPOSTA = 380

CRIATIVIDADE = 0.3


# ==========================================
# GEMINI
# ==========================================

# As credenciais continuam no .env.

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
).strip()

WEB_ENDERECO = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)

WEB_MODELO = GEMINI_MODEL

WEB_ARQUIVO_DA_CHAVE = "chave_web.txt"

WEB_TEMPO_MAXIMO = 120

WEB_SE_FALHAR_USAR_LOCAL = False

WEB_OPCOES_EXTRAS = {}


# ==========================================
# RESUMIDOR DA AULA
# ==========================================

IA_TEMPERATURA = 0.2

# Uma requisição por processamento.
# Não repetir automaticamente em caso de erro.

IA_MAX_TENTATIVAS = 1

ARQUIVO_PERSONALIDADE = (
    PASTA_ROBO / "personalidade.txt"
)

ARQUIVO_ESQUEMA = (
    PASTA_ROBO / "esquema_resumo.json"
)


# ==========================================
# SERVIDOR
# ==========================================

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORTA = int(
    os.getenv("PORT", "8000")
)

PORT = PORTA

# As configurações específicas dos dois
# microfones e HTTPS ficam no config_audio.py.


# ==========================================
# CONFIGURAÇÕES DE E-MAIL
# ==========================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv("SMTP_PORT", "587")
)

SMTP_USER = os.getenv(
    "SMTP_USER",
    ""
).strip()

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD",
    ""
).strip()

SMTP_NOME = os.getenv(
    "SMTP_NOME",
    "Agente de Acessibilidade Educacional"
)

SMTP_TIMEOUT = int(
    os.getenv("SMTP_TIMEOUT", "30")
)

SMTP_USE_TLS = True

SMTP_USE_SSL = False


# ==========================================
# DESTINATÁRIOS
# ==========================================

DESTINATARIOS = [

    email.strip()

    for email in os.getenv(
        "DESTINATARIOS",
        ""
    ).split(",")

    if email.strip()

]


# ==========================================
# ACESSIBILIDADE
# ==========================================

LEGENDAS_ATIVADAS = True

SALVAR_TRANSCRICOES = True

SALVAR_RESUMOS = True

SALVAR_PDFS = True

ENVIO_EMAIL_AUTOMATICO = True

RESETAR_SESSAO_APOS_PROCESSAMENTO = True


# ==========================================
# VISÃO - COMPATIBILIDADE ORIGINAL
# ==========================================

# Desativada, pois nosso projeto utiliza
# somente áudio e texto.

VISAO_LIGADA = False

VISAO_OLHOS_SEGUEM = False

VISAO_RECONHECER_PESSOAS = False

VISAO_CUMPRIMENTAR_CONHECIDOS = False

VISAO_CUMPRIMENTAR_DESCONHECIDOS = False

VISAO_MINUTOS_ENTRE_CUMPRIMENTOS = 30

VISAO_SEGUNDOS_DE_SALA_VAZIA = 120

VISAO_FOTO_PARA_WEB = False

VISAO_MODELO_LOCAL = None

VISAO_CONTAR_NOMES_PARA_IA = False

VISAO_OLHAR_QUEM_FALA = False

VISAO_MAO_LEVANTADA = False

VISAO_SEGUNDOS_COM_A_MAO_LEVANTADA = 1.5

VISAO_SEGUNDOS_ENTRE_VEZES = 6

VISAO_LARGURA_DO_QUADRO = 480

VISAO_QUADROS_POR_SEGUNDO = 2

VISAO_QUADROS_POR_SEGUNDO_EM_GRUPO = 2

VISAO_SEGUNDOS_OLHANDO_QUEM_FALOU = 3

VISAO_MOVIMENTO_MINIMO_DA_BOCA = 4

VISAO_CERTEZA_DA_MAO = 0.5

VISAO_TAMANHO_MINIMO_DO_ROSTO = 40

VISAO_LIMIAR_DE_PARECIDO = 0.40

VISAO_FOTOS_POR_CADASTRO = 6

VISAO_TEMPO_MAXIMO_WEB = 25

VISAO_WEB_MODELO = None

MODELO_DETECTOR_DE_ROSTOS = (
    "modelos/visao/face_detection_yunet_2023mar.onnx"
)

MODELO_RECONHECEDOR_DE_ROSTOS = (
    "modelos/visao/face_recognition_sface_2021dec.onnx"
)

MODELO_DETECTOR_DE_PALMAS = (
    "modelos/visao/palm_detection_mediapipe_2023feb.onnx"
)

ARQUIVO_DE_ROSTOS = "dados/rostos.json"

PASTA_DE_FOTOS = "fotos"


# ==========================================
# FRASES ORIGINAIS DO ROBÔ
# ==========================================

CUMPRIMENTOS = [
    "Oi, {nome}!",
    "Olá, {nome}! Que bom te ver.",
    "E aí, {nome}? Tudo bem?"
]

CUMPRIMENTOS_DESCONHECIDOS = [
    "Oi! Tudo bem?",
    "Olá! Se precisar de mim, é só dizer ei robô."
]

FRASES_DA_VEZ = [
    "Pode falar, {nome}!",
    "Oi, {nome}! Pode falar."
]

FRASES_DA_VEZ_SEM_NOME = [
    "Pode falar!",
    "Vi sua mão. Pode falar!"
]


# ==========================================
# BUSCA DE IMAGENS
# ==========================================

IMAGENS_LIGADAS = False

IMAGENS_FONTES = [
    "wikipedia",
    "commons"
]

IMAGENS_CONTATO = ""

IMAGENS_SEGUNDOS_NA_TELA = 60

IMAGENS_VERIFICAR_COM_IA = False

IMAGENS_EXPLICAR = False

IMAGENS_IDIOMA_DA_WIKIPEDIA = "pt"

IMAGENS_RESULTADOS = 8

IMAGENS_TAMANHO = 1280

IMAGENS_TEMPO_MAXIMO = 10


# ==========================================
# ROSTO E TELA
# ==========================================

ROSTO_IA_ESCOLHE_EXPRESSAO = False

ROSTO_SEGUNDOS_DE_EXPRESSAO = 6

ROSTO_SEGUNDOS_PARA_SONO = 60

TELA_IA_PODE_MOSTRAR = False

TELA_SEGUNDOS_NA_TELA = 60


# ==========================================
# SÍNTESE DE VOZ
# ==========================================

VOZ_PIPER = (
    "modelos/piper/pt_BR-faber-medium.onnx"
)


# ==========================================
# PREPARAR DIRETÓRIOS
# ==========================================

def preparar_diretorios():
    """
    Cria os diretórios necessários para
    armazenamento e processamento.
    """

    diretorios = [

        PASTA_DADOS,

        PASTA_TRANSCRICOES,

        PASTA_RELATORIOS,

        PASTA_RESUMOS,

        PASTA_PENDENCIAS,

        PASTA_MODELOS,

        PASTA_WHISPER,

        PASTA_CERTIFICADOS

    ]

    for diretorio in diretorios:

        Path(diretorio).mkdir(

            parents=True,

            exist_ok=True

        )


# ==========================================
# VALIDAR RECONHECIMENTO DE VOZ
# ==========================================

def validar_reconhecimento():
    """
    Verifica os modelos locais e o executável
    do Whisper.

    Retorna uma lista de erros encontrados.
    """

    erros = []

    if not Path(MODELO_VOSK).is_dir():

        erros.append(

            f"Modelo Vosk não encontrado: "
            f"{MODELO_VOSK}"

        )

    if VOSK_TAXA_AMOSTRAGEM != 16000:

        erros.append(

            "A taxa do Vosk deve ser 16000 Hz."

        )

    if VOSK_TAMANHO_BLOCO <= 0:

        erros.append(

            "VOSK_TAMANHO_BLOCO inválido."

        )

    if VOSK_TAMANHO_FILA <= 0:

        erros.append(

            "VOSK_TAMANHO_FILA inválido."

        )

    if MOTOR_ENTENDIMENTO == "whisper":

        if not ARQUIVO_MODELO_WHISPER.is_file():

            erros.append(

                "Modelo Whisper não encontrado: "
                f"{ARQUIVO_MODELO_WHISPER}"

            )

        if not WHISPER_EXECUTAVEL.is_file():

            erros.append(

                "Executável Whisper não encontrado: "
                f"{WHISPER_EXECUTAVEL}"

            )

        elif not os.access(

            WHISPER_EXECUTAVEL,

            os.X_OK

        ):

            erros.append(

                "Executável Whisper não possui "
                "permissão de execução."

            )

        if WHISPER_THREADS < 1:

            erros.append(

                "WHISPER_THREADS deve ser maior que zero."

            )

        if WHISPER_MAX_SEGUNDOS <= 0:

            erros.append(

                "WHISPER_MAX_SEGUNDOS inválido."

            )

        if WHISPER_TIMEOUT <= 0:

            erros.append(

                "WHISPER_TIMEOUT inválido."

            )

    if not APELIDOS_COMANDOS:

        erros.append(

            "Nenhum comando de voz configurado."

        )

    return erros


# ==========================================
# VALIDAR GEMINI E E-MAIL
# ==========================================

def validar_configuracao():
    """
    Valida as configurações necessárias para
    geração e envio do material.
    """

    erros = []

    # ======================================
    # GEMINI
    # ======================================

    if not GEMINI_API_KEY:

        erros.append(

            "GEMINI_API_KEY não configurada."

        )

    if not GEMINI_MODEL:

        erros.append(

            "GEMINI_MODEL não configurado."

        )

    if not ARQUIVO_PERSONALIDADE.is_file():

        erros.append(

            "personalidade.txt não encontrado."

        )

    if not ARQUIVO_ESQUEMA.is_file():

        erros.append(

            "esquema_resumo.json não encontrado."

        )

    if IA_MAX_TENTATIVAS < 1:

        erros.append(

            "IA_MAX_TENTATIVAS deve ser maior que zero."

        )

    # ======================================
    # SMTP
    # ======================================

    if ENVIO_EMAIL_AUTOMATICO:

        if not SMTP_HOST:

            erros.append(

                "SMTP_HOST não configurado."

            )

        if not SMTP_USER:

            erros.append(

                "SMTP_USER não configurado."

            )

        if not SMTP_PASSWORD:

            erros.append(

                "SMTP_PASSWORD não configurado."

            )

        if not DESTINATARIOS:

            erros.append(

                "Nenhum destinatário configurado."

            )

        if SMTP_PORT <= 0:

            erros.append(

                "SMTP_PORT inválida."

            )

    return erros


# ==========================================
# VALIDAR CONFIGURAÇÃO COMPLETA
# ==========================================

def validar_tudo():

    erros = []

    erros.extend(
        validar_reconhecimento()
    )

    erros.extend(
        validar_configuracao()
    )

    return erros


# ==========================================
# EXIBIR CONFIGURAÇÃO
# ==========================================

def exibir_configuracao():
    """
    Exibe informações de diagnóstico.

    Não mostra chaves de API nem senhas.
    """

    print("\n" + "=" * 65)

    print("AGENTE IHC - CONFIGURAÇÕES")

    print("=" * 65)

    print(
        f"\nDiretório principal: {BASE_DIR}"
    )

    print(
        f"Idioma: {IDIOMA}"
    )

    print(
        f"Servidor: {HOST}:{PORTA}"
    )

    print("\n--- Reconhecimento de voz ---")

    print(
        f"Motor: {MOTOR_ENTENDIMENTO}"
    )

    print(
        f"Vosk: {MODELO_VOSK}"
    )

    print(
        f"Vosk encontrado: "
        f"{Path(MODELO_VOSK).is_dir()}"
    )

    print(
        f"Taxa: {VOSK_TAXA_AMOSTRAGEM} Hz"
    )

    print(
        f"Dispositivo físico: {VOSK_DISPOSITIVO}"
    )

    print(
        f"Whisper: {ARQUIVO_MODELO_WHISPER}"
    )

    print(
        f"Modelo encontrado: "
        f"{ARQUIVO_MODELO_WHISPER.is_file()}"
    )

    print(
        f"Executável: {WHISPER_EXECUTAVEL}"
    )

    print(
        f"Executável encontrado: "
        f"{WHISPER_EXECUTAVEL.is_file()}"
    )

    print(
        f"Threads Whisper: {WHISPER_THREADS}"
    )

    print(
        f"Idioma Whisper: {WHISPER_IDIOMA}"
    )

    print(
        f"Tradução: {WHISPER_TRADUZIR}"
    )

    print(
        f"Vocabulários: "
        f"{len(VOCABULARIOS_DISCIPLINAS)}"
    )

    print("\n--- Comandos de voz ---")

    for comando, apelidos in APELIDOS_COMANDOS.items():

        print(
            f"{comando}: {len(apelidos)} variações"
        )

    print("\n--- Gemini ---")

    print(
        f"Modelo: {GEMINI_MODEL}"
    )

    print(

        "API configurada: "

        + (

            "Sim"

            if GEMINI_API_KEY

            else "Não"

        )

    )

    print(
        f"Tentativas por processamento: "
        f"{IA_MAX_TENTATIVAS}"
    )

    print("\n--- E-mail ---")

    print(
        f"Servidor: {SMTP_HOST}:{SMTP_PORT}"
    )

    print(

        "Usuário configurado: "

        + (

            "Sim"

            if SMTP_USER

            else "Não"

        )

    )

    print(

        "Senha configurada: "

        + (

            "Sim"

            if SMTP_PASSWORD

            else "Não"

        )

    )

    print(
        f"Destinatários: {len(DESTINATARIOS)}"
    )

    print(
        f"Envio automático: "
        f"{ENVIO_EMAIL_AUTOMATICO}"
    )

    print("\n--- Armazenamento ---")

    print(
        f"Transcrições: {PASTA_TRANSCRICOES}"
    )

    print(
        f"Resumos: {PASTA_RESUMOS}"
    )

    print(
        f"Relatórios: {PASTA_RELATORIOS}"
    )

    print(
        f"Pendências: {PASTA_PENDENCIAS}"
    )

    print("\n--- Validação ---")

    erros = validar_tudo()

    if erros:

        for erro in erros:

            print(
                f"[ERRO] {erro}"
            )

    else:

        print(
            "[OK] Configurações verificadas."
        )

    print("\n" + "=" * 65)

    return erros


# ==========================================
# EXECUÇÃO ISOLADA
# ==========================================

if __name__ == "__main__":

    preparar_diretorios()

    exibir_configuracao()