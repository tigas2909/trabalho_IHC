"""
Configurações do Agente de Acessibilidade Educacional.
Projeto IHC - IFPR.

Baseado no Robô Byte para TV Box B13.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ==========================================
# Diretório principal
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ==========================================
# Identidade
# ==========================================

NOME_DO_ROBO = "Agente IHC"

PALAVRAS_DE_ATIVACAO = [
    "ei robô",
    "eu robô",
    "oi robô",
    "olá robô",
    "byte",
    "oi byte"
]


# ==========================================
# Ouvido
# ==========================================

MODELO_VOSK = "modelos/vosk-model-small-pt-0.3"

TAXA_DE_AMOSTRAGEM = 16000

LIMIAR_DE_SILENCIO = 600

SEGUNDOS_DE_SILENCIO_PARA_PARAR = 1

SEGUNDOS_MAXIMOS_DE_FALA = 25

SEGUNDOS_ESPERANDO_PERGUNTA = 4


# ==========================================
# Reconhecimento de fala
# ==========================================

MOTOR_ENTENDIMENTO = "parakeet"

PASTA_PARAKEET = "modelos/parakeet-ptBR"

PARAKEET_QUANTIZACAO = "int8"


# ==========================================
# Whisper
# ==========================================

MODELO_WHISPER = "base"

PASTA_WHISPER = "modelos/whisper"

DICA_WHISPER = (
    "Aula acadêmica em português brasileiro. "
    "Professor explicando conceitos, atividades "
    "e trabalhos."
)

CAPRICHO_DO_WHISPER = 3

NUCLEOS_DO_PROCESSADOR = 4

SO_OFFLINE = True


# ==========================================
# Cérebro original
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
# Inteligência Artificial - Gemini
# ==========================================

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
# Configuração do resumidor
# ==========================================

IA_TEMPERATURA = 0.2

IA_MAX_TENTATIVAS = 2

ARQUIVO_PERSONALIDADE = (
    BASE_DIR / "robo" / "personalidade.txt"
)

ARQUIVO_ESQUEMA = (
    BASE_DIR / "robo" / "esquema_resumo.json"
)


# ==========================================
# Comandos da aula
# ==========================================

COMANDO_INICIO = "iniciar aula"

COMANDO_ATIVIDADE = "iniciar atividade"

COMANDO_TRABALHO = "iniciar trabalho"

COMANDO_CONTINUAR = "continuar aula"

COMANDO_FINAL = "finalizar aula"


# ==========================================
# Diretórios
# ==========================================

PASTA_DADOS = BASE_DIR / "dados"

PASTA_TRANSCRICOES = (
    PASTA_DADOS / "transcricoes"
)

PASTA_RELATORIOS = (
    PASTA_DADOS / "relatorios"
)

PASTA_RESUMOS = (
    PASTA_DADOS / "resumos"
)

PASTA_PENDENCIAS = (
    PASTA_DADOS / "pendencias"
)

PASTA_MODELOS = BASE_DIR / "modelos"

PASTA_INTERFACE = BASE_DIR / "interface"


# ==========================================
# Servidor
# ==========================================

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORTA = int(
    os.getenv("PORT", "8000")
)

PORT = PORTA


# ==========================================
# Configurações de e-mail
# ==========================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv("SMTP_PORT", "587")
)

SMTP_USER = os.getenv("SMTP_USER")

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

SMTP_NOME = os.getenv(
    "SMTP_NOME",
    "Agente de Acessibilidade Educacional"
)

SMTP_TIMEOUT = int(
    os.getenv("SMTP_TIMEOUT", "30")
)


# ==========================================
# Destinatários
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
# Visão - Recursos originais do professor
# ==========================================

# Desativados porque nosso agente trabalha
# exclusivamente com áudio e texto.

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
# Frases originais do robô
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
# Busca de imagens
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
# Rosto e tela
# ==========================================

ROSTO_IA_ESCOLHE_EXPRESSAO = False

ROSTO_SEGUNDOS_DE_EXPRESSAO = 6

ROSTO_SEGUNDOS_PARA_SONO = 60

TELA_IA_PODE_MOSTRAR = False

TELA_SEGUNDOS_NA_TELA = 60


# ==========================================
# Síntese de voz original
# ==========================================

VOZ_PIPER = (
    "modelos/piper/pt_BR-faber-medium.onnx"
)


# ==========================================
# Configurações de acessibilidade
# ==========================================

IDIOMA = "pt-BR"

LEGENDAS_ATIVADAS = True

SALVAR_TRANSCRICOES = True

SALVAR_RESUMOS = True

SALVAR_PDFS = True

ENVIO_EMAIL_AUTOMATICO = True

RESETAR_SESSAO_APOS_PROCESSAMENTO = True


# ==========================================
# Armazenamento
# ==========================================

def preparar_diretorios():

    diretorios = [

        PASTA_DADOS,

        PASTA_TRANSCRICOES,

        PASTA_RELATORIOS,

        PASTA_RESUMOS,

        PASTA_PENDENCIAS
    ]

    for diretorio in diretorios:

        diretorio.mkdir(
            parents=True,
            exist_ok=True
        )


# ==========================================
# Validação da configuração
# ==========================================

def validar_configuracao():

    erros = []

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

    if ENVIO_EMAIL_AUTOMATICO:

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

    return erros