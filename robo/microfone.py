"""
Captura contínua de áudio do Agente IHC.

Vosk:
    Reconhecimento de comandos e legendas parciais.

Whisper:
    Transcrição multilíngue do conteúdo acadêmico.

O registro começa somente após "iniciar aula".
"""

import json
import queue
import threading

from pathlib import Path

import sounddevice as sd

from vosk import Model, KaldiRecognizer, SetLogLevel

from robo import config
from robo.escuta import Escuta
from robo.whisper import Whisper


class Microfone:

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

        self.modelo = None

        self.whisper = None

        self.escuta = Escuta()

        self.thread = None

        self.parar_evento = threading.Event()

        self.audio_perdido = threading.Event()

        self.taxa = config.VOSK_TAXA_AMOSTRAGEM

        self.dispositivo = config.VOSK_DISPOSITIVO

        self.tamanho_bloco = config.VOSK_TAMANHO_BLOCO

        self.fila = queue.Queue(
            maxsize=config.VOSK_TAMANHO_FILA
        )

        self.max_bytes = (
            self.taxa
            * 2
            * config.WHISPER_MAX_SEGUNDOS
        )

    # ==========================================
    # ESTADO
    # ==========================================

    @property
    def ativo(self):

        return (
            self.thread is not None
            and self.thread.is_alive()
            and not self.parar_evento.is_set()
        )

    def notificar(self, estado, mensagem):

        print(
            f"[MICROFONE] {mensagem}"
        )

        if self.ao_status:

            self.ao_status(
                estado,
                mensagem
            )

    # ==========================================
    # CARREGAR MODELOS
    # ==========================================

    def carregar_modelos(self):

        if self.modelo is None:

            caminho = Path(
                config.MODELO_VOSK
            )

            if not caminho.is_dir():

                raise FileNotFoundError(
                    f"Modelo Vosk não encontrado:\n"
                    f"{caminho}"
                )

            self.notificar(
                "carregando",
                "Carregando modelo Vosk..."
            )

            SetLogLevel(
                config.VOSK_NIVEL_LOG
            )

            self.modelo = Model(
                str(caminho)
            )

        if self.whisper is None:

            self.whisper = Whisper()

        self.notificar(
            "pronto",
            "Vosk e Whisper configurados."
        )

    # ==========================================
    # CALLBACK DE CAPTURA
    # ==========================================

    def callback_audio(
        self,
        indata,
        frames,
        time_info,
        status
    ):

        if self.parar_evento.is_set():

            return

        if status.input_overflow:

            self.audio_perdido.set()

        try:

            self.fila.put_nowait(
                bytes(indata)
            )

        except queue.Full:

            self.audio_perdido.set()

    # ==========================================
    # INICIAR RECONHECIMENTO
    # ==========================================

    def iniciar(self):

        if (
            self.thread
            and self.thread.is_alive()
        ):

            return False

        self.parar_evento.clear()

        self.audio_perdido.clear()

        self.fila = queue.Queue(
            maxsize=config.VOSK_TAMANHO_FILA
        )

        self.thread = threading.Thread(
            target=self._executar,
            daemon=True,
            name="Microfone-IHC"
        )

        self.thread.start()

        return True

    # ==========================================
    # CRIAR RECONHECEDOR
    # ==========================================

    def criar_reconhecedor(
        self,
        registrando=False
    ):

        if registrando:

            # Vocabulário completo durante a aula.

            reconhecedor = KaldiRecognizer(
                self.modelo,
                self.taxa
            )

        else:

            # Vocabulário restrito enquanto
            # aguarda o comando de início.

            vocabulario = json.dumps(
                config.VOSK_VOCABULARIO_ATIVACAO,
                ensure_ascii=False
            )

            reconhecedor = KaldiRecognizer(
                self.modelo,
                self.taxa,
                vocabulario
            )

        reconhecedor.SetWords(True)

        return reconhecedor

    # ==========================================
    # ENTREGAR TEXTO
    # ==========================================

    def entregar_texto(self, texto):

        texto = texto.strip()

        if not texto:

            return

        if self.parar_evento.is_set():

            return

        if self.ao_texto:

            self.ao_texto(texto)

    # ==========================================
    # ENTREGAR RESULTADO PARCIAL
    # ==========================================

    def entregar_parcial(self, texto):

        if (
            self.ao_parcial
            and config.VOSK_RESULTADOS_PARCIAIS
        ):

            self.ao_parcial(texto)

    # ==========================================
    # PROCESSAR TRECHO DE ÁUDIO
    # ==========================================

    def processar_trecho(
        self,
        texto_vosk,
        audio,
        registrando
    ):

        texto_vosk = texto_vosk.strip()

        comando = self.escuta.identificar(
            texto_vosk
        )

        # --------------------------------------
        # Aguardando início.
        # --------------------------------------

        if not registrando:

            if comando == config.COMANDO_INICIO:

                print(
                    "[VOSK] Comando de início detectado."
                )

                self.entregar_texto(comando)

            return

        # --------------------------------------
        # Comandos durante a aula.
        # --------------------------------------

        if comando:

            print(
                f"[VOSK] Comando: {comando}"
            )

            self.entregar_texto(comando)

            return

        # --------------------------------------
        # Conteúdo acadêmico.
        # --------------------------------------

        if not audio:

            return

        if not self.esta_registrando():

            return

        # Evita enviar silêncio ao Whisper.
        # Verifica o volume sem depender apenas
        # do reconhecimento de palavras do Vosk.

        if not texto_vosk and not self.tem_voz(audio):

            return

        try:

            texto = self.whisper.transcrever(
                audio
            )

            if not texto.strip():

                texto = texto_vosk

        except Exception as erro:

            if not config.WHISPER_FALLBACK_VOSK:

                raise

            self.notificar(
                "aviso",
                f"Whisper falhou: {erro}. "
                "Utilizando Vosk."
            )

            texto = texto_vosk

        if not self.esta_registrando():

            return

        self.entregar_texto(texto)

    # ==========================================
    # DETECTAR ATIVIDADE DE ÁUDIO
    # ==========================================

    def tem_voz(self, audio):

        import numpy as np

        if not audio:

            return False

        amostras = np.frombuffer(
            audio,
            dtype=np.int16
        ).astype(np.float32)

        if amostras.size == 0:

            return False

        # Verifica blocos de aproximadamente
        # 100 milissegundos.

        tamanho = self.taxa // 10

        for inicio in range(
            0,
            len(amostras),
            tamanho
        ):

            bloco = amostras[
                inicio:inicio + tamanho
            ]

            volume = float(
                np.sqrt(
                    np.mean(bloco ** 2)
                )
            )

            if volume >= config.LIMIAR_DE_SILENCIO:

                return True

        return False

    # ==========================================
    # RECONHECIMENTO CONTÍNUO
    # ==========================================

    def _executar(self):

        erro_fatal = False

        try:

            self.carregar_modelos()

            if self.parar_evento.is_set():

                return

            registrando = bool(
                self.esta_registrando()
            )

            reconhecedor = self.criar_reconhecedor(
                registrando
            )

            audio_aula = bytearray()

            ultimo_parcial = ""

            with sd.RawInputStream(
                samplerate=self.taxa,
                blocksize=self.tamanho_bloco,
                device=self.dispositivo,
                dtype="int16",
                channels=1,
                callback=self.callback_audio
            ):

                self.notificar(
                    "escutando",
                    "Microfone ativo. "
                    "Aguardando iniciar aula."
                )

                while not self.parar_evento.is_set():

                    # ----------------------------------
                    # Verificar perda de áudio.
                    # ----------------------------------

                    if self.audio_perdido.is_set():

                        raise RuntimeError(
                            "Perda de áudio detectada. "
                            "O processamento não conseguiu "
                            "acompanhar a captura."
                        )

                    try:

                        bloco = self.fila.get(
                            timeout=0.2
                        )

                    except queue.Empty:

                        continue

                    # ----------------------------------
                    # Verificar estado atual da aula.
                    # ----------------------------------

                    estado_atual = bool(
                        self.esta_registrando()
                    )

                    if estado_atual != registrando:

                        registrando = estado_atual

                        reconhecedor = (
                            self.criar_reconhecedor(
                                registrando
                            )
                        )

                        audio_aula.clear()

                        ultimo_parcial = ""

                        self.entregar_parcial("")

                    # ----------------------------------
                    # Guardar áudio somente durante
                    # uma aula ativa.
                    # ----------------------------------

                    if registrando:

                        audio_aula.extend(bloco)

                    terminou = (
                        reconhecedor.AcceptWaveform(
                            bloco
                        )
                    )

                    limite = (
                        registrando
                        and len(audio_aula)
                        >= self.max_bytes
                    )

                    # ----------------------------------
                    # Resultado definitivo.
                    # ----------------------------------

                    if terminou or limite:

                        if terminou:

                            resultado = json.loads(
                                reconhecedor.Result()
                            )

                        else:

                            resultado = json.loads(
                                reconhecedor.FinalResult()
                            )

                        texto_vosk = resultado.get(
                            "text",
                            ""
                        )

                        self.processar_trecho(
                            texto_vosk,
                            bytes(audio_aula),
                            registrando
                        )

                        audio_aula.clear()

                        ultimo_parcial = ""

                        self.entregar_parcial("")

                        # O comando anterior pode ter
                        # iniciado ou finalizado a aula.

                        registrando = bool(
                            self.esta_registrando()
                        )

                        reconhecedor = (
                            self.criar_reconhecedor(
                                registrando
                            )
                        )

                    # ----------------------------------
                    # Resultado parcial.
                    # ----------------------------------

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

            self.notificar(
                "erro",
                str(erro)
            )

        finally:

            self.parar_evento.set()

            if not erro_fatal:

                self.notificar(
                    "parado",
                    "Reconhecimento encerrado."
                )

    # ==========================================
    # ENCERRAR
    # ==========================================

    def parar(self):

        self.parar_evento.set()

    def aguardar(self, timeout=5):

        if self.thread:

            self.thread.join(
                timeout=timeout
            )

    # ==========================================
    # STATUS
    # ==========================================

    def obter_status(self):

        return {

            "ativo": self.ativo,

            "registrando": bool(
                self.esta_registrando()
            ),

            "vosk_carregado": (
                self.modelo is not None
            ),

            "whisper_configurado": (
                self.whisper is not None
            ),

            "taxa_amostragem": self.taxa,

            "dispositivo": self.dispositivo,

            "fila_audio": self.fila.qsize(),

            "audio_perdido": (
                self.audio_perdido.is_set()
            )

        }


# ==========================================
# TESTE DIRETO
# ==========================================

if __name__ == "__main__":

    import time

    escuta = Escuta()

    def receber_texto(texto):

        resultado = escuta.processar(texto)

        if not resultado:

            return

        if resultado["tipo"] == "comando":

            comando = resultado["texto"]

            print(
                f"\n[COMANDO] {comando}"
            )

            if comando == config.COMANDO_INICIO:

                escuta.ativar()

            elif comando == config.COMANDO_FINAL:

                escuta.desativar()

        else:

            print(
                f"\n[LEGENDA] {resultado['texto']}"
            )

    def receber_parcial(texto):

        if escuta.registrando and texto:

            print(
                f"\r[PARCIAL] {texto}",
                end="",
                flush=True
            )

    microfone = Microfone(
        ao_texto=receber_texto,
        ao_parcial=receber_parcial,
        esta_registrando=lambda: escuta.registrando
    )

    print("=" * 50)

    print("TESTE DO MICROFONE - VOSK + WHISPER")

    print("=" * 50)

    microfone.iniciar()

    try:

        while microfone.ativo:

            time.sleep(0.5)

    except KeyboardInterrupt:

        print("\nEncerrando...")

    finally:

        microfone.parar()

        microfone.aguardar()