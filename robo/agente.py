from pathlib import Path
from datetime import datetime
from threading import RLock

from .aula import Aula
from .comandos import Comandos, Comando


class Agente:

    def __init__(self, diretorio=None):

        self.aula = Aula()

        self.comandos = Comandos(
            self.aula
        )

        self.diretorio = diretorio

        self.ouvintes = []

        self.ultima_legenda = ""

        self.ultimo_arquivo = None

        self.lock = RLock()

        self.total_transcricoes = 0

    # ==========================================
    # Sistema de eventos
    # ==========================================

    def adicionar_ouvinte(self, callback):

        if not callable(callback):
            raise TypeError(
                "O ouvinte deve ser uma função."
            )

        with self.lock:

            if callback not in self.ouvintes:

                self.ouvintes.append(callback)

    def remover_ouvinte(self, callback):

        with self.lock:

            if callback in self.ouvintes:

                self.ouvintes.remove(callback)

    def emitir_evento(self, tipo, dados=None):

        evento = {
            "tipo": tipo,
            "dados": dados,
            "horario": datetime.now()
                .astimezone()
                .isoformat()
        }

        with self.lock:

            ouvintes = self.ouvintes.copy()

        for callback in ouvintes:

            try:

                callback(evento)

            except Exception as erro:

                print(
                    f"[Agente] Erro no ouvinte: {erro}"
                )

        return evento

    # ==========================================
    # Processamento das transcrições
    # ==========================================

    def processar_transcricao(self, texto):

        if not isinstance(texto, str):

            raise TypeError(
                "A transcrição deve ser uma string."
            )

        texto = texto.strip()

        if not texto:

            return {
                "tipo": "ignorado",
                "motivo": "Transcrição vazia."
            }

        with self.lock:

            self.total_transcricoes += 1

            resultado = self.comandos.processar(
                texto
            )

            if resultado["tipo"] == "comando":

                return self._processar_comando(
                    resultado
                )

            return self._processar_fala(
                texto
            )

    # ==========================================
    # Processamento de falas
    # ==========================================

    def _processar_fala(self, texto):

        if not self.aula.esta_ativa():

            return {
                "tipo": "ignorado",
                "motivo": "Nenhuma aula em andamento."
            }

        registro = self.aula.registrar(
            texto
        )

        self.ultima_legenda = texto

        evento = {
            "texto": texto,
            "registro": registro,
            "estado": self.aula.estado.value,
            "aula_id": self.aula.id
        }

        self.emitir_evento(
            "legenda",
            evento
        )

        print(f"[Legenda] {texto}")

        return {
            "tipo": "legenda",
            "dados": evento
        }

    # ==========================================
    # Processamento dos comandos
    # ==========================================

    def _processar_comando(self, resultado):

        comando = resultado["comando"]

        execucao = resultado["resultado"]

        if not execucao["sucesso"]:

            self.emitir_evento(
                "comando_rejeitado",
                execucao
            )

            return {
                "tipo": "comando",
                "sucesso": False,
                "dados": execucao
            }

        if comando == Comando.INICIO.value:

            self.ultima_legenda = ""

            self.ultimo_arquivo = None

            self.emitir_evento(
                "aula_iniciada",
                self.aula.obter_status()
            )

        elif comando == Comando.FINAL.value:

            return self._finalizar_aula(
                execucao
            )

        else:

            self.emitir_evento(
                "estado_alterado",
                self.aula.obter_status()
            )

        self.emitir_evento(
            "comando_executado",
            execucao
        )

        return {
            "tipo": "comando",
            "sucesso": True,
            "dados": execucao
        }

    # ==========================================
    # Finalização e armazenamento
    # ==========================================

    def _finalizar_aula(self, execucao):

        dados = self.aula.exportar()

        self.emitir_evento(
            "aula_finalizada",
            dados
        )

        try:

            arquivo = self.aula.salvar(
                self.diretorio
            )

            self.ultimo_arquivo = arquivo

        except Exception as erro:

            self.emitir_evento(
                "erro_armazenamento",
                {
                    "aula_id": self.aula.id,
                    "erro": str(erro)
                }
            )

            return {
                "tipo": "finalizacao",
                "sucesso": False,
                "dados": dados,
                "erro": str(erro)
            }

        resultado = {
            "tipo": "finalizacao",
            "sucesso": True,
            "dados": dados,
            "arquivo": str(arquivo)
        }

        self.emitir_evento(
            "transcricao_salva",
            {
                "aula_id": self.aula.id,
                "arquivo": str(arquivo)
            }
        )

        self.emitir_evento(
            "resumo_pendente",
            dados
        )

        print(
            "[Agente] Aula finalizada e salva."
        )

        return resultado

    # ==========================================
    # Controle manual
    # ==========================================

    def iniciar_aula(
        self,
        titulo="Aula",
        professor="Não informado",
        disciplina="Não informada"
    ):

        with self.lock:

            self.aula.iniciar(
                titulo=titulo,
                professor=professor,
                disciplina=disciplina
            )

            self.ultima_legenda = ""

            self.ultimo_arquivo = None

            status = self.aula.obter_status()

            self.emitir_evento(
                "aula_iniciada",
                status
            )

            return status

    def finalizar_aula(self):

        return self.processar_transcricao(
            "finalizar aula"
        )

    # ==========================================
    # Status do agente
    # ==========================================

    def obter_status(self):

        with self.lock:

            return {
                "agente": "Agente IHC",
                "aula": self.aula.obter_status(),
                "ultima_legenda": self.ultima_legenda,
                "total_transcricoes": (
                    self.total_transcricoes
                ),
                "ultimo_arquivo": (
                    str(self.ultimo_arquivo)
                    if self.ultimo_arquivo
                    else None
                )
            }

    def obter_transcricao(self):

        with self.lock:

            return self.aula.exportar()

    def salvar_progresso(self):

        with self.lock:

            if self.aula.id is None:

                return None

            arquivo = self.aula.salvar(
                self.diretorio
            )

            self.ultimo_arquivo = arquivo

            return arquivo