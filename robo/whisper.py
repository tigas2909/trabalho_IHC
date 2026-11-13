"""
Módulo de reconhecimento de fala utilizando Whisper.cpp.

Projeto IHC - IFPR.

Responsabilidades:
- Transcrever áudio localmente.
- Reconhecer português brasileiro e termos em inglês.
- Contextualizar a transcrição por disciplina.
- Utilizar modelo quantizado.
- Não depender de conexão com a internet.
"""

import os
import subprocess
import tempfile
import time
import wave

from pathlib import Path
from threading import Lock

from robo import config


# ==========================================
# EXCEÇÕES
# ==========================================

class ErroWhisper(Exception):

    pass


class ErroModeloWhisper(ErroWhisper):

    pass


class ErroTranscricaoWhisper(ErroWhisper):

    pass


# ==========================================
# WHISPER
# ==========================================

class Whisper:

    def __init__(self, disciplina=None):

        self.executavel = Path(
            config.WHISPER_EXECUTAVEL
        )

        self.modelo = Path(
            config.ARQUIVO_MODELO_WHISPER
        )

        self.taxa = 16000

        self.idioma = config.WHISPER_IDIOMA

        self.threads = config.WHISPER_THREADS

        self.timeout = config.WHISPER_TIMEOUT

        self.disciplina = (
            disciplina
            or config.DISCIPLINA_PADRAO
        )

        self.lock = Lock()

        # Estatísticas de processamento.

        self.total_transcricoes = 0

        self.total_erros = 0

        self.total_segundos_audio = 0.0

        self.total_tempo_processamento = 0.0

        self.ultima_transcricao = None

        self.validar()

        print(
            "[WHISPER] Inicializado."
        )

        print(
            f"[WHISPER] Modelo: {self.modelo.name}"
        )

        print(
            f"[WHISPER] Idioma: {self.idioma}"
        )

        print(
            f"[WHISPER] Threads: {self.threads}"
        )


    # ==========================================
    # VALIDAR INSTALAÇÃO
    # ==========================================

    def validar(self):

        if not self.executavel.is_file():

            raise ErroModeloWhisper(

                "Executável Whisper não encontrado:\n"

                f"{self.executavel}"

            )

        if not os.access(
            self.executavel,
            os.X_OK
        ):

            raise ErroModeloWhisper(

                "Executável Whisper sem permissão "
                "de execução."

            )

        if not self.modelo.is_file():

            raise ErroModeloWhisper(

                "Modelo Whisper não encontrado:\n"

                f"{self.modelo}"

            )

        if self.modelo.stat().st_size == 0:

            raise ErroModeloWhisper(

                "O arquivo do modelo está vazio."

            )

        if self.threads < 1:

            raise ErroModeloWhisper(

                "A quantidade de threads deve "
                "ser maior que zero."

            )

        if self.timeout < 1:

            raise ErroModeloWhisper(

                "O timeout deve ser maior que zero."

            )

        return True


    # ==========================================
    # CONFIGURAR DISCIPLINA
    # ==========================================

    def definir_disciplina(self, disciplina):

        if not isinstance(disciplina, str):

            raise ValueError(

                "A disciplina deve ser uma string."

            )

        disciplina = disciplina.strip().lower()

        if not disciplina:

            disciplina = config.DISCIPLINA_PADRAO

        if disciplina not in (
            config.VOCABULARIOS_DISCIPLINAS
        ):

            disciplina = config.DISCIPLINA_PADRAO

        self.disciplina = disciplina

        print(

            f"[WHISPER] Disciplina: "
            f"{self.disciplina}"

        )

        return self.disciplina


    # ==========================================
    # OBTER VOCABULÁRIO
    # ==========================================

    def obter_vocabulario(
        self,
        vocabulario=None
    ):

        if vocabulario is not None:

            if not isinstance(
                vocabulario,
                str
            ):

                raise ValueError(

                    "O vocabulário deve ser texto."

                )

            return vocabulario.strip()

        return config.obter_vocabulario(

            self.disciplina

        ).strip()


    # ==========================================
    # VALIDAR ÁUDIO
    # ==========================================

    def validar_audio(self, audio):

        if not isinstance(

            audio,

            (bytes, bytearray, memoryview)

        ):

            raise TypeError(

                "O áudio deve estar em formato "
                "PCM representado por bytes."

            )

        audio = bytes(audio)

        if not audio:

            return b""

        # PCM int16 utiliza dois bytes
        # para cada amostra.

        if len(audio) % 2 != 0:

            raise ValueError(

                "O áudio PCM possui tamanho inválido "
                "para amostras de 16 bits."

            )

        return audio


    # ==========================================
    # CALCULAR DURAÇÃO
    # ==========================================

    def calcular_duracao(self, audio):

        return (

            len(audio)

            / 2

            / self.taxa

        )


    # ==========================================
    # SALVAR ÁUDIO WAV
    # ==========================================

    def salvar_wav(

        self,

        audio,

        caminho

    ):

        audio = self.validar_audio(

            audio

        )

        caminho = Path(caminho)

        with wave.open(

            str(caminho),

            "wb"

        ) as arquivo:

            # Áudio mono.

            arquivo.setnchannels(1)

            # PCM de 16 bits.

            arquivo.setsampwidth(2)

            # Frequência de 16 kHz.

            arquivo.setframerate(

                self.taxa

            )

            arquivo.writeframes(

                audio

            )

        return caminho


    # ==========================================
    # MONTAR COMANDO WHISPER.CPP
    # ==========================================

    def montar_comando(

        self,

        arquivo_audio,

        arquivo_saida,

        vocabulario

    ):

        comando = [

            str(self.executavel),

            # Modelo quantizado.

            "-m",

            str(self.modelo),

            # Arquivo de áudio.

            "-f",

            str(arquivo_audio),

            # Idioma principal.

            "-l",

            self.idioma,

            # Quantidade de threads.

            "-t",

            str(self.threads),

            # Não imprimir informações
            # de processamento no terminal.

            "-np",

            # Gerar arquivo de texto.

            "-otxt",

            # Caminho da saída.

            "-of",

            str(arquivo_saida)

        ]

        # Contexto técnico de programação.

        if vocabulario:

            comando.extend([

                "--prompt",

                vocabulario

            ])

        # Não mostrar timestamps.

        if config.WHISPER_SEM_TIMESTAMPS:

            comando.append("-nt")

        # Por padrão, não traduzir.
        # Preservar o idioma original.

        if config.WHISPER_TRADUZIR:

            comando.append("-tr")

        return comando


    # ==========================================
    # EXECUTAR RECONHECIMENTO
    # ==========================================

    def executar(self, comando):

        try:

            resultado = subprocess.run(

                comando,

                capture_output=True,

                text=True,

                encoding="utf-8",

                errors="replace",

                timeout=self.timeout,

                shell=False,

                check=False

            )

        except subprocess.TimeoutExpired as erro:

            raise ErroTranscricaoWhisper(

                "O Whisper ultrapassou o tempo "
                f"máximo de {self.timeout} segundos."

            ) from erro

        except FileNotFoundError as erro:

            raise ErroModeloWhisper(

                "Executável Whisper não encontrado."

            ) from erro

        except OSError as erro:

            raise ErroTranscricaoWhisper(

                f"Não foi possível executar "
                f"o Whisper: {erro}"

            ) from erro

        if resultado.returncode != 0:

            mensagem = (

                resultado.stderr

                or resultado.stdout

                or "Erro desconhecido."

            )

            raise ErroTranscricaoWhisper(

                "Whisper retornou um erro:\n"

                + mensagem[-3000:]

            )

        return resultado


    # ==========================================
    # LIMPAR RESULTADO
    # ==========================================

    def limpar_texto(self, texto):

        if not texto:

            return ""

        texto = texto.replace(

            "\ufeff",

            ""

        )

        linhas = []

        for linha in texto.splitlines():

            linha = linha.strip()

            if linha:

                linhas.append(linha)

        texto = " ".join(linhas)

        texto = " ".join(

            texto.split()

        )

        # Não registrar marcadores comuns
        # de ausência de fala.

        ignorar = {

            "[silêncio]",

            "[silencio]",

            "[silence]",

            "[blank_audio]",

            "[inaudível]",

            "[inaudivel]",

            "(silêncio)",

            "(silence)"

        }

        if texto.lower() in ignorar:

            return ""

        return texto.strip()


    # ==========================================
    # ATUALIZAR ESTATÍSTICAS
    # ==========================================

    def registrar_estatisticas(

        self,

        texto,

        duracao_audio,

        tempo_processamento

    ):

        self.total_transcricoes += 1

        self.total_segundos_audio += (

            duracao_audio

        )

        self.total_tempo_processamento += (

            tempo_processamento

        )

        fator_tempo_real = 0.0

        if duracao_audio > 0:

            fator_tempo_real = (

                tempo_processamento

                / duracao_audio

            )

        self.ultima_transcricao = {

            "texto": texto,

            "disciplina": self.disciplina,

            "duracao_audio": round(

                duracao_audio,

                3

            ),

            "tempo_processamento": round(

                tempo_processamento,

                3

            ),

            "fator_tempo_real": round(

                fator_tempo_real,

                3

            ),

            "modelo": self.modelo.name

        }


    # ==========================================
    # TRANSCRIÇÃO PRINCIPAL
    # ==========================================

    def transcrever(

        self,

        audio,

        vocabulario=None

    ):

        audio = self.validar_audio(

            audio

        )

        if not audio:

            return ""

        duracao_audio = (

            self.calcular_duracao(audio)

        )

        prompt = self.obter_vocabulario(

            vocabulario

        )

        # Impede que duas transcrições
        # sejam executadas simultaneamente.

        with self.lock:

            inicio = time.perf_counter()

            try:

                # Arquivos temporários são removidos
                # automaticamente após a execução.

                with tempfile.TemporaryDirectory(

                    prefix="ihc_whisper_"

                ) as pasta:

                    pasta = Path(pasta)

                    arquivo_audio = (

                        pasta / "audio.wav"

                    )

                    arquivo_saida = (

                        pasta / "transcricao"

                    )

                    arquivo_texto = (

                        pasta / "transcricao.txt"

                    )

                    # Converter PCM em WAV.

                    self.salvar_wav(

                        audio,

                        arquivo_audio

                    )

                    # Preparar execução.

                    comando = self.montar_comando(

                        arquivo_audio,

                        arquivo_saida,

                        prompt

                    )

                    # Executar modelo local.

                    self.executar(

                        comando

                    )

                    # Verificar resultado.

                    if not arquivo_texto.is_file():

                        raise ErroTranscricaoWhisper(

                            "O Whisper não gerou "
                            "o arquivo de transcrição."

                        )

                    texto = arquivo_texto.read_text(

                        encoding="utf-8",

                        errors="replace"

                    )

                    texto = self.limpar_texto(

                        texto

                    )

                tempo_processamento = (

                    time.perf_counter()

                    - inicio

                )

                self.registrar_estatisticas(

                    texto,

                    duracao_audio,

                    tempo_processamento

                )

                print(

                    f"[WHISPER] "

                    f"Áudio: {duracao_audio:.2f}s | "

                    f"Processamento: "

                    f"{tempo_processamento:.2f}s"

                )

                return texto

            except Exception:

                self.total_erros += 1

                raise


    # ==========================================
    # TRANSCRIBIR ARQUIVO WAV
    # ==========================================

    def transcrever_arquivo(

        self,

        arquivo,

        vocabulario=None

    ):

        arquivo = Path(arquivo)

        if not arquivo.is_file():

            raise FileNotFoundError(

                f"Áudio não encontrado: {arquivo}"

            )

        with wave.open(

            str(arquivo),

            "rb"

        ) as wav:

            if wav.getnchannels() != 1:

                raise ValueError(

                    "O arquivo deve possuir "
                    "apenas um canal de áudio."

                )

            if wav.getsampwidth() != 2:

                raise ValueError(

                    "O áudio deve utilizar PCM "
                    "de 16 bits."

                )

            if wav.getframerate() != self.taxa:

                raise ValueError(

                    "O áudio deve possuir "
                    "taxa de 16000 Hz."

                )

            audio = wav.readframes(

                wav.getnframes()

            )

        return self.transcrever(

            audio,

            vocabulario

        )


    # ==========================================
    # OBTER ESTATÍSTICAS
    # ==========================================

    def obter_estatisticas(self):

        tempo_medio = 0.0

        fator_tempo_real = 0.0

        if self.total_transcricoes > 0:

            tempo_medio = (

                self.total_tempo_processamento

                / self.total_transcricoes

            )

        if self.total_segundos_audio > 0:

            fator_tempo_real = (

                self.total_tempo_processamento

                / self.total_segundos_audio

            )

        return {

            "modelo": self.modelo.name,

            "idioma": self.idioma,

            "disciplina": self.disciplina,

            "threads": self.threads,

            "total_transcricoes": (

                self.total_transcricoes

            ),

            "total_erros": self.total_erros,

            "total_segundos_audio": round(

                self.total_segundos_audio,

                3

            ),

            "total_tempo_processamento": round(

                self.total_tempo_processamento,

                3

            ),

            "tempo_medio_processamento": round(

                tempo_medio,

                3

            ),

            "fator_tempo_real": round(

                fator_tempo_real,

                3

            ),

            "ultima_transcricao": (

                self.ultima_transcricao

            )

        }


    # ==========================================
    # RESETAR ESTATÍSTICAS
    # ==========================================

    def resetar_estatisticas(self):

        with self.lock:

            self.total_transcricoes = 0

            self.total_erros = 0

            self.total_segundos_audio = 0.0

            self.total_tempo_processamento = 0.0

            self.ultima_transcricao = None


    # ==========================================
    # ENCERRAR
    # ==========================================

    def fechar(self):

        # O executável é iniciado e encerrado
        # em cada transcrição.
        #
        # Não existe um processo permanente
        # para finalizar nesta implementação.

        print(

            "[WHISPER] Encerrado."

        )


# ==========================================
# TESTE DIRETO DO MÓDULO
# ==========================================

if __name__ == "__main__":

    import argparse
    import json

    parser = argparse.ArgumentParser(

        description=(

            "Teste do reconhecimento local "

            "Whisper para aulas de programação."

        )

    )

    parser.add_argument(

        "--audio",

        type=str,

        default=None,

        help="Arquivo WAV mono, PCM 16 bits, 16 kHz."

    )

    parser.add_argument(

        "--disciplina",

        type=str,

        default=config.DISCIPLINA_PADRAO,

        help="Disciplina para contextualização."

    )

    argumentos = parser.parse_args()

    print()

    print("=" * 60)

    print("TESTE DO WHISPER")

    print("=" * 60)

    try:

        whisper = Whisper(

            disciplina=argumentos.disciplina

        )

        print()

        print("[OK] Modelo encontrado.")

        print("[OK] Executável encontrado.")

        print()

        print("VOCABULÁRIO UTILIZADO:")

        print("-" * 60)

        print(

            whisper.obter_vocabulario()

        )

        if argumentos.audio:

            print()

            print("TRANSCRIÇÃO:")

            print("-" * 60)

            texto = whisper.transcrever_arquivo(

                argumentos.audio

            )

            print(texto)

            print()

            print("ESTATÍSTICAS:")

            print("-" * 60)

            print(

                json.dumps(

                    whisper.obter_estatisticas(),

                    ensure_ascii=False,

                    indent=4

                )

            )

        else:

            print()

            print(

                "Nenhum áudio informado."

            )

            print(

                "Instalação validada com sucesso."

            )

        whisper.fechar()

    except Exception as erro:

        print()

        print(

            f"[ERRO] {erro}"

        )

        raise SystemExit(1)