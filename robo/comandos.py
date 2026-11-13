import re
import unicodedata

from enum import Enum

from .aula import Aula


class Comando(Enum):

    INICIO = "inicio"
    ATIVIDADE = "atividade"
    TRABALHO = "trabalho"
    CONTINUAR = "continuar"
    FINAL = "final"

class Comandos:

    def __init__(self, aula: Aula):

        self.aula = aula

        self.comandos = {
            "iniciar aula": Comando.INICIO,
            "inicio da aula": Comando.INICIO,

            "iniciar atividade": Comando.ATIVIDADE,
            "inicio da atividade": Comando.ATIVIDADE,

            "iniciar trabalho": Comando.TRABALHO,
            "inicio do trabalho": Comando.TRABALHO,

            "continuar aula": Comando.CONTINUAR,
            "retomar aula": Comando.CONTINUAR,

            "finalizar aula": Comando.FINAL,
            "encerrar aula": Comando.FINAL,
            "fim da aula": Comando.FINAL
        }

    # ==========================================
    # Normalização do texto
    # ==========================================

    @staticmethod
    def normalizar(texto):

        if not isinstance(texto, str):
            raise TypeError(
                "O texto deve ser uma string."
            )

        texto = texto.lower().strip()

        texto = unicodedata.normalize(
            "NFKD",
            texto
        )

        texto = "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(caractere)
        )

        texto = re.sub(
            r"[^\w\s]",
            " ",
            texto
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto.strip()

    # ==========================================
    # Identificação do comando
    # ==========================================

    def identificar(self, texto):

        texto = self.normalizar(texto)

        return self.comandos.get(texto)

    # ==========================================
    # Validação do comando
    # ==========================================

    def validar(self, comando):

        if comando == Comando.INICIO:

            return not self.aula.esta_ativa()

        if comando in (
            Comando.ATIVIDADE,
            Comando.TRABALHO,
            Comando.CONTINUAR,
            Comando.FINAL
        ):

            return self.aula.esta_ativa()

        return False

    # ==========================================
    # Execução do comando
    # ==========================================

    def executar(self, comando):

        if not isinstance(comando, Comando):
            raise ValueError(
                "Comando inválido."
            )

        if not self.validar(comando):

            return {
                "sucesso": False,
                "comando": comando.value,
                "mensagem": (
                    "Comando não permitido "
                    "no estado atual."
                )
            }

        dados = None

        if comando == Comando.INICIO:

            dados = self.aula.iniciar()

        elif comando == Comando.ATIVIDADE:

            self.aula.iniciar_atividade()

        elif comando == Comando.TRABALHO:

            self.aula.iniciar_trabalho()

        elif comando == Comando.CONTINUAR:

            self.aula.continuar_aula()

        elif comando == Comando.FINAL:

            dados = self.aula.finalizar()

        print(
            f"[Comandos] Executado: {comando.value}"
        )

        return {
            "sucesso": True,
            "comando": comando.value,
            "estado": self.aula.estado.value,
            "mensagem": "Comando executado.",
            "dados": dados
        }

    # ==========================================
    # Processamento da transcrição
    # ==========================================

    def processar(self, texto):

        comando = self.identificar(texto)

        if comando is None:

            return {
                "tipo": "transcricao",
                "texto": texto,
                "comando": None
            }

        resultado = self.executar(comando)

        return {
            "tipo": "comando",
            "texto": texto,
            "comando": comando.value,
            "resultado": resultado
        }
        