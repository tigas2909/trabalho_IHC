"""
Controlador de escuta do Agente IHC.

Responsabilidades:
- Identificar comandos de voz.
- Controlar a ativação da aula.
- Ignorar conversas antes do início.
- Separar comandos do conteúdo didático.
- Continuar aguardando após finalizar.
"""

import unicodedata

from threading import RLock

from robo import config


class Escuta:

    def __init__(self):

        self._registrando = False

        self.lock = RLock()

        self.comandos = {}

        self.carregar_comandos()


    # ==========================================
    # CARREGAR COMANDOS DO CONFIG
    # ==========================================

    def carregar_comandos(self):

        self.comandos.clear()

        for comando, apelidos in (
            config.APELIDOS_COMANDOS.items()
        ):

            self.comandos[
                self.normalizar(comando)
            ] = comando

            for apelido in apelidos:

                self.comandos[
                    self.normalizar(apelido)
                ] = comando


    # ==========================================
    # ESTADO DO REGISTRO
    # ==========================================

    @property
    def registrando(self):

        with self.lock:

            return self._registrando


    # ==========================================
    # NORMALIZAR TEXTO
    # ==========================================

    @staticmethod
    def normalizar(texto):

        if not isinstance(texto, str):

            return ""

        texto = unicodedata.normalize(

            "NFD",

            texto.lower()

        )

        # Remover acentos.

        texto = "".join(

            caractere

            for caractere in texto

            if unicodedata.category(
                caractere
            ) != "Mn"

        )

        # Remover pontuação.

        texto = "".join(

            caractere

            if (
                caractere.isalnum()
                or caractere.isspace()
            )

            else " "

            for caractere in texto

        )

        # Remover espaços duplicados.

        return " ".join(
            texto.split()
        )


    # ==========================================
    # IDENTIFICAR COMANDO
    # ==========================================

    def identificar(self, texto):

        normalizado = self.normalizar(
            texto
        )

        if not normalizado:

            return None

        return self.comandos.get(
            normalizado
        )


    # ==========================================
    # ATIVAR REGISTRO
    # ==========================================

    def ativar(self):

        with self.lock:

            if self._registrando:

                return False

            self._registrando = True

        print(
            "[ESCUTA] Registro da aula ativado."
        )

        return True


    # ==========================================
    # DESATIVAR REGISTRO
    # ==========================================

    def desativar(self):

        with self.lock:

            if not self._registrando:

                return False

            self._registrando = False

        print(
            "[ESCUTA] Registro da aula encerrado."
        )

        print(
            "[ESCUTA] Aguardando nova aula."
        )

        return True


    # ==========================================
    # PROCESSAR TEXTO RECONHECIDO
    # ==========================================

    def processar(self, texto):

        if not isinstance(texto, str):

            return None

        texto = texto.strip()

        if not texto:

            return None

        comando = self.identificar(
            texto
        )

        with self.lock:

            registrando = self._registrando

        # --------------------------------------
        # Aguardando início da aula.
        # --------------------------------------

        if not registrando:

            if comando == config.COMANDO_INICIO:

                return {

                    "tipo": "comando",

                    "texto": comando

                }

            # Ignorar conversas e outros comandos.

            return None

        # --------------------------------------
        # Aula ativa: verificar comandos.
        # --------------------------------------

        if comando:

            return {

                "tipo": "comando",

                "texto": comando

            }

        # --------------------------------------
        # Conteúdo normal da aula.
        # --------------------------------------

        return {

            "tipo": "legenda",

            "texto": texto

        }


    # ==========================================
    # STATUS
    # ==========================================

    def obter_status(self):

        return {

            "registrando": self.registrando,

            "estado": (

                "registrando"

                if self.registrando

                else "aguardando"

            ),

            "comandos_disponiveis": list(

                config.APELIDOS_COMANDOS.keys()

            )

        }


    # ==========================================
    # RESETAR
    # ==========================================

    def resetar(self):

        with self.lock:

            self._registrando = False

        print(
            "[ESCUTA] Controlador resetado."
        )


# ==========================================
# TESTE DIRETO
# ==========================================

if __name__ == "__main__":

    escuta = Escuta()

    print("=" * 50)

    print("TESTE DO CONTROLADOR DE ESCUTA")

    print("=" * 50)

    frases = [

        "Bom dia, pessoal.",

        "Iniciar aula!",

        "Hoje vamos estudar Java e Spring Boot.",

        "Isso é importante.",

        "Utilizem a anotação RestController.",

        "Iniciar atividade.",

        "Criem uma API REST.",

        "Continuar aula.",

        "Agora vamos estudar JSON.",

        "Finalizar aula.",

        "Até a próxima aula.",

        "Iniciar aula."

    ]

    for frase in frases:

        print(
            f"\nEntrada: {frase}"
        )

        resultado = escuta.processar(
            frase
        )

        if resultado is None:

            print(
                "Resultado: ignorado."
            )

            continue

        print(
            f"Resultado: {resultado}"
        )

        if resultado["tipo"] == "comando":

            comando = resultado["texto"]

            if comando == config.COMANDO_INICIO:

                escuta.ativar()

            elif comando == config.COMANDO_FINAL:

                escuta.desativar()

    print()

    print("=" * 50)

    print("STATUS FINAL")

    print("=" * 50)

    print(
        escuta.obter_status()
    )
