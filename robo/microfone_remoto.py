"""
Microfone remoto do Agente IHC.

Recebe áudio PCM do navegador via WebSocket.

Formato:
    PCM signed int16
    Mono
    16000 Hz

Utiliza Vosk para comandos e resultados parciais.
Utiliza Whisper para transcrições definitivas.

Não utiliza sounddevice nem microfone físico.
"""

import json
import queue
import threading

import numpy as np

from vosk import Model, KaldiRecognizer, SetLogLevel

from robo import config
from robo import config_audio
from robo.escuta import Escuta
from robo.whisper import Whisper


class MicrofoneRemoto:

    def __init__(
        self,
        ao_texto=None,
        ao_parcial=None,
        ao_status=None,
        esta_registrando=None
    ):

        self.ao_texto = ao_texto
        self.ao_parcial = ao_parcial
        self.ao_status = ao_status

        self.esta_registrando = (
            esta_registrando or (lambda: False)
        )

        self.taxa = config_audio.AUDIO_TAXA

        self.max_bytes = (
            self.taxa
            * 2
            * config_audio.AUDIO_MAX_SEGUNDOS
        )

        self.fila = queue.Queue(
            maxsize=config_audio.AUDIO_FILA_MAX
        )

        self.parar_evento = threading.Event()

        self.pronto = threading.Event()

        self.audio_perdido = threading.Event()

        self.lock = threading.RLock()

        self.thread = None

        self.modelo_vosk = None

        self.whisper = None

        self.escuta = Escuta()

        self.disciplina = "geral"

        self.erro_inicializacao = None

        self.estado = "parado"

        self.mensagem = "Microfone remoto desligado."

        self.total_blocos = 0

        self.total_bytes = 0

        self.total_transcricoes = 0

    # ======================================
    # PROPRIEDADES
    # ======================================

    @property
    def ativo(self):

        return bool(
            self.thread is not None
            and self.thread.is_alive()
            and not self.parar_evento.is_set()
        )

    # ======================================
    # STATUS
    # ======================================

    def notificar(self, estado, mensagem):

        self.estado = estado
        self.mensagem = mensagem

        print(
            f"[MICROFONE REMOTO] {mensagem}"
        )

        if callable(self.ao_status):

            try:
                self.ao_status(estado, mensagem)

            except Exception as erro:
                print(
                    f"[ERRO STATUS] {erro}"
                )

    def obter_status(self):

        return {
            "ativo": self.ativo,
            "pronto": self.pronto.is_set(),
            "estado": self.estado,
            "mensagem": self.mensagem,
            "total_blocos": self.total_blocos,
            "total_bytes": self.total_bytes,
            "total_transcricoes": (
                self.total_transcricoes
            ),
            "fila": self.fila.qsize(),
            "disciplina": self.disciplina
        }

    # ======================================
    # VOCABULÁRIO
    # ======================================

    def definir_disciplina(self, disciplina):

        self.disciplina = disciplina or "geral"

        if self.whisper:

            self.whisper.definir_disciplina(
                self.disciplina
            )

    # ======================================
    # LIMPAR FILA
    # ======================================

    def limpar_fila(self):

        while True:

            try:
                self.fila.get_nowait()

            except queue.Empty:
                break

    # ======================================
    # CARREGAR MODELOS
    # ======================================

    def carregar_modelos(self):

        SetLogLevel(
            getattr(config, "VOSK_NIVEL_LOG", -1)
        )

        if self.modelo_vosk is None:

            self.notificar(
                "carregando",
                "Carregando modelo Vosk..."
            )

            caminho = str(
                config.MODELO_VOSK
            )

            self.modelo_vosk = Model(caminho)

        if self.whisper is None:

            self.notificar(
                "carregando",
                "Inicializando Whisper..."
            )

            self.whisper = Whisper(
                disciplina=self.disciplina
            )

        self.whisper.definir_disciplina(
            self.disciplina
        )

    # ======================================
    # RECONHECEDOR VOSK
    # ======================================

    def criar_reconhecedor(self, registrando):

        if registrando:

            reconhecedor = KaldiRecognizer(
                self.modelo_vosk,
                self.taxa
            )

        else:

            vocabulario = getattr(
                config,
                "VOSK_VOCABULARIO_ATIVACAO",
                [
                    "iniciar aula",
                    "começar aula",
                    "início da aula",
                    "[unk]"
                ]
            )

            reconhecedor = KaldiRecognizer(
                self.modelo_vosk,
                self.taxa,
                json.dumps(
                    vocabulario,
                    ensure_ascii=False
                )
            )

        reconhecedor.SetWords(True)

        return reconhecedor

    # ======================================
    # VERIFICAR VOZ
    # ======================================

    def tem_voz(self, audio):

        if not audio or len(audio) < 2:
            return False

        amostras = np.frombuffer(
            audio,
            dtype="<i2"
        ).astype(np.float32)

        if amostras.size == 0:
            return False

        rms = np.sqrt(
            np.mean(amostras ** 2)
        )

        return bool(
            rms >= (
                config_audio.AUDIO_LIMIAR_SILENCIO
            )
        )

    # ======================================
    # ENTREGAR TEXTO
    # ======================================

    def entregar_texto(self, texto):

        texto = str(texto or "").strip()

        if not texto:
            return

        if self.parar_evento.is_set():
            return

        if callable(self.ao_texto):

            self.ao_texto(texto)

    def entregar_parcial(self, texto):

        if self.parar_evento.is_set():
            return

        if callable(self.ao_parcial):

            self.ao_parcial(
                str(texto or "")
            )

    # ======================================
    # PROCESSAR TRECHO DEFINITIVO
    # ======================================

    def processar_trecho(
        self,
        texto_vosk,
        audio,
        registrando
    ):

        texto_vosk = str(
            texto_vosk or ""
        ).strip()

        comando = self.escuta.identificar(
            texto_vosk
        )

        # Vosk controla a ativação.
        if not registrando:

            if comando == "iniciar aula":

                self.entregar_texto(comando)

            return

        # Comandos não precisam passar pelo
        # Whisper.
        if comando:

            self.entregar_texto(comando)

            return

        # Não processar silêncio desnecessário.
        if not self.tem_voz(audio):

            return

        texto_final = ""

        try:

            if self.whisper:

                resultado = (
                    self.whisper.transcrever(audio)
                )

                # Compatibilidade com retorno
                # em string ou dicionário.
                if isinstance(resultado, str):

                    texto_final = resultado

                elif isinstance(resultado, dict):

                    texto_final = (
                        resultado.get("texto")
                        or resultado.get("text")
                        or ""
                    )

        except Exception as erro:

            print(
                f"[WHISPER REMOTO] {erro}"
            )

        texto_final = str(
            texto_final or ""
        ).strip()

        # Se Whisper falhar, utiliza o Vosk.
        if (
            not texto_final
            and getattr(
                config,
                "WHISPER_FALLBACK_VOSK",
                True
            )
        ):

            texto_final = texto_vosk

        if not texto_final:
            return

        # Evita entregar trechos de uma aula
        # que foi finalizada manualmente.
        if not self.esta_registrando():
            return

        self.total_transcricoes += 1

        self.entregar_texto(texto_final)

    # ======================================
    # RECEBER ÁUDIO DO NAVEGADOR
    # ======================================

    def receber_audio(self, audio):

        if not self.ativo:
            return False

        if not self.pronto.is_set():
            return False

        if not isinstance(audio, bytes):
            return False

        if not audio or len(audio) % 2:
            return False

        if (
            len(audio)
            > config_audio.AUDIO_MAX_BYTES
        ):
            return False

        try:

            self.fila.put_nowait(audio)

            self.total_blocos += 1

            self.total_bytes += len(audio)

            return True

        except queue.Full:

            self.audio_perdido.set()

            return False

    # ======================================
    # INICIAR MICROFONE
    # ======================================

    def iniciar(self):

        with self.lock:

            if (
                self.thread
                and self.thread.is_alive()
            ):

                return False

            self.parar_evento.clear()

            self.pronto.clear()

            self.audio_perdido.clear()

            self.erro_inicializacao = None

            self.limpar_fila()

            self.total_blocos = 0

            self.total_bytes = 0

            self.total_transcricoes = 0

            self.thread = threading.Thread(
                target=self._executar,
                name="microfone-remoto",
                daemon=True
            )

            self.thread.start()

            return True

    # ======================================
    # PARAR MICROFONE
    # ======================================

    def parar(self):

        self.parar_evento.set()

        self.pronto.clear()

    def aguardar(self, timeout=5):

        thread = self.thread

        if (
            thread
            and thread is not threading.current_thread()
        ):

            thread.join(timeout=timeout)

        return not bool(
            thread and thread.is_alive()
        )

    # ======================================
    # LOOP DE RECONHECIMENTO
    # ======================================

    def _executar(self):

        erro_fatal = False

        try:

            self.carregar_modelos()

            if self.parar_evento.is_set():
                return

            registrando = bool(
                self.esta_registrando()
            )

            reconhecedor = (
                self.criar_reconhecedor(
                    registrando
                )
            )

            audio_trecho = bytearray()

            ultimo_parcial = ""

            self.pronto.set()

            self.notificar(
                "escutando",
                "Microfone do celular pronto."
            )

            while not self.parar_evento.is_set():

                if self.audio_perdido.is_set():

                    raise RuntimeError(
                        "Fila de áudio sobrecarregada. "
                        "O reconhecimento está mais lento "
                        "que a transmissão."
                    )

                try:

                    bloco = self.fila.get(
                        timeout=0.2
                    )

                except queue.Empty:

                    continue

                estado_atual = bool(
                    self.esta_registrando()
                )

                # Detecta alterações manuais
                # no estado da aula.
                if estado_atual != registrando:

                    registrando = estado_atual

                    reconhecedor = (
                        self.criar_reconhecedor(
                            registrando
                        )
                    )

                    audio_trecho.clear()

                    ultimo_parcial = ""

                    self.entregar_parcial("")

                if registrando:

                    audio_trecho.extend(bloco)

                terminou = (
                    reconhecedor.AcceptWaveform(
                        bloco
                    )
                )

                limite = (
                    registrando
                    and len(audio_trecho)
                    >= self.max_bytes
                )

                # ==============================
                # RESULTADO DEFINITIVO
                # ==============================

                if terminou or limite:

                    if terminou:

                        resultado = json.loads(
                            reconhecedor.Result()
                        )

                    else:

                        resultado = json.loads(
                            reconhecedor.FinalResult()
                        )

                    texto = resultado.get(
                        "text",
                        ""
                    )

                    self.processar_trecho(
                        texto,
                        bytes(audio_trecho),
                        registrando
                    )

                    audio_trecho.clear()

                    ultimo_parcial = ""

                    self.entregar_parcial("")

                    registrando = bool(
                        self.esta_registrando()
                    )

                    reconhecedor = (
                        self.criar_reconhecedor(
                            registrando
                        )
                    )

                # ==============================
                # RESULTADO PARCIAL
                # ==============================

                elif registrando:

                    resultado = json.loads(
                        reconhecedor.PartialResult()
                    )

                    parcial = resultado.get(
                        "partial",
                        ""
                    ).strip()

                    if parcial != ultimo_parcial:

                        ultimo_parcial = parcial

                        self.entregar_parcial(
                            parcial
                        )

        except Exception as erro:

            erro_fatal = True

            self.erro_inicializacao = str(erro)

            self.notificar(
                "erro",
                str(erro)
            )

        finally:

            self.parar_evento.set()

            self.pronto.clear()

            self.limpar_fila()

            if not erro_fatal:

                self.notificar(
                    "parado",
                    "Microfone remoto desligado."
                )


# ==========================================
# TESTE ISOLADO
# ==========================================

if __name__ == "__main__":

    microfone = MicrofoneRemoto(
        ao_texto=lambda texto: print(
            f"[TEXTO] {texto}"
        )
    )

    print(
        "Classe MicrofoneRemoto inicializada."
    )

    print(
        "Para transmitir áudio, utilize "
        "o painel do professor."
    )

    print(
        microfone.obter_status()
    )