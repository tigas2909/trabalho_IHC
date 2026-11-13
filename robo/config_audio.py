"""
Configurações das fontes de áudio do Agente IHC.
"""

from pathlib import Path

# ==========================================
# DIRETÓRIOS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

PASTA_CERTIFICADOS = BASE_DIR / "certificados"

CERTIFICADO_SERVIDOR = (
    PASTA_CERTIFICADOS / "servidor.pem"
)

CHAVE_SERVIDOR = (
    PASTA_CERTIFICADOS / "servidor-key.pem"
)

# ==========================================
# REDE
# ==========================================

HOST = "0.0.0.0"

PORTA = 8000

IP_SERVIDOR = "192.168.0.14"

IPS_PROFESSORES = {
    "127.0.0.1",
    "::1",
    "::ffff:127.0.0.1",
    "192.168.0.11"
}

# ==========================================
# FONTES DE ÁUDIO
# ==========================================

MICROFONE_LOCAL_ATIVADO = True

MICROFONE_REMOTO_ATIVADO = True

# Opções: "local" ou "remoto"
MICROFONE_MODO_PADRAO = "remoto"

# Se o modo padrão for local, iniciar
# automaticamente o microfone físico.
ESCUTA_LOCAL_AUTOMATICA = True

# ==========================================
# ÁUDIO REMOTO
# ==========================================

AUDIO_TAXA = 16000

AUDIO_CANAIS = 1

AUDIO_BITS = 16

AUDIO_BLOCO = 4000

AUDIO_MAX_BYTES = 32000

AUDIO_FILA_MAX = 120

AUDIO_MAX_SEGUNDOS = 12

# Volume RMS mínimo para considerar
# que um trecho contém voz.
AUDIO_LIMIAR_SILENCIO = 200

AUDIO_TIMEOUT_MODELO = 30

AUDIO_TIMEOUT_ENCERRAMENTO = 15

ROTA_AUDIO = "/ws/professor/audio"

# ==========================================
# SEGURANÇA
# ==========================================

EXIGIR_HTTPS_REMOTO = True


def obter_origens_permitidas():
    """
    Retorna os endereços autorizados para
    acessar as APIs e o WebSocket de áudio.
    """

    enderecos = {
        IP_SERVIDOR,
        "localhost",
        "127.0.0.1",
        "[::1]"
    }

    return {
        f"{protocolo}://{endereco}:{PORTA}"
        for protocolo in ("http", "https")
        for endereco in enderecos
    }


def possui_certificados():
    """
    Verifica se os certificados HTTPS existem.
    """

    return (
        CERTIFICADO_SERVIDOR.is_file()
        and CHAVE_SERVIDOR.is_file()
    )