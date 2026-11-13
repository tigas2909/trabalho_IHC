import json

from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4


class EstadoAula(Enum):
    AGUARDANDO = "aguardando"
    CONTEUDO = "conteudo"
    ATIVIDADE = "atividade"
    TRABALHO = "trabalho"
    FINALIZADO = "finalizado"


class Aula:

    def __init__(self):

        self.id = None
        self.titulo = None
        self.professor = None
        self.disciplina = None

        self.estado = EstadoAula.AGUARDANDO

        self.inicio = None
        self.fim = None

        self.registros = []

    # ==========================================
    # Controle da aula
    # ==========================================

    def iniciar(
        self,
        titulo="Aula",
        professor="Não informado",
        disciplina="Não informada"
    ):

        if self.esta_ativa():
            raise RuntimeError(
                "Já existe uma aula em andamento."
            )

        self.id = str(uuid4())

        self.titulo = titulo
        self.professor = professor
        self.disciplina = disciplina

        self.inicio = datetime.now().astimezone()
        self.fim = None

        self.registros = []

        self.estado = EstadoAula.CONTEUDO

        print(f"[Aula] Aula iniciada: {self.titulo}")

        return self.id

    def finalizar(self):

        if not self.esta_ativa():
            raise RuntimeError(
                "Não existe uma aula em andamento."
            )

        self.fim = datetime.now().astimezone()

        self.estado = EstadoAula.FINALIZADO

        print("[Aula] Aula finalizada.")

        return self.exportar()

    # ==========================================
    # Controle de estados
    # ==========================================

    def esta_ativa(self):

        return self.estado in (
            EstadoAula.CONTEUDO,
            EstadoAula.ATIVIDADE,
            EstadoAula.TRABALHO
        )

    def alterar_estado(self, estado):

        if not isinstance(estado, EstadoAula):
            raise ValueError("Estado inválido.")

        if not self.esta_ativa():
            raise RuntimeError(
                "Não existe uma aula em andamento."
            )

        estados_permitidos = (
            EstadoAula.CONTEUDO,
            EstadoAula.ATIVIDADE,
            EstadoAula.TRABALHO
        )

        if estado not in estados_permitidos:
            raise ValueError(
                "Utilize iniciar() ou finalizar() "
                "para controlar a sessão."
            )

        self.estado = estado

        print(
            f"[Aula] Estado alterado: {estado.value}"
        )

    def iniciar_atividade(self):

        self.alterar_estado(
            EstadoAula.ATIVIDADE
        )

    def iniciar_trabalho(self):

        self.alterar_estado(
            EstadoAula.TRABALHO
        )

    def continuar_aula(self):

        self.alterar_estado(
            EstadoAula.CONTEUDO
        )

    # ==========================================
    # Registro das transcrições
    # ==========================================

    def registrar(self, texto):

        if not self.esta_ativa():
            return None

        if not isinstance(texto, str):
            raise TypeError(
                "A transcrição deve ser uma string."
            )

        texto = texto.strip()

        if not texto:
            return None

        registro = {
            "id": len(self.registros) + 1,
            "tipo": self.estado.value,
            "texto": texto,
            "horario": datetime.now()
                .astimezone()
                .isoformat()
        }

        self.registros.append(registro)

        return registro

    # ==========================================
    # Recuperação dos conteúdos
    # ==========================================

    def obter_registros(self, tipo=None):

        if tipo is None:
            return [
                registro.copy()
                for registro in self.registros
            ]

        if isinstance(tipo, EstadoAula):
            tipo = tipo.value

        return [
            registro.copy()
            for registro in self.registros
            if registro["tipo"] == tipo
        ]

    def obter_conteudo(self):

        return self.obter_registros(
            EstadoAula.CONTEUDO
        )

    def obter_atividades(self):

        return self.obter_registros(
            EstadoAula.ATIVIDADE
        )

    def obter_trabalhos(self):

        return self.obter_registros(
            EstadoAula.TRABALHO
        )

    def obter_transcricao_completa(self):

        return "\n".join(
            registro["texto"]
            for registro in self.registros
        )

    # ==========================================
    # Informações da aula
    # ==========================================

    def obter_duracao(self):

        if self.inicio is None:
            return 0

        horario_final = (
            self.fim or datetime.now().astimezone()
        )

        duracao = horario_final - self.inicio

        return int(duracao.total_seconds())

    def obter_status(self):

        return {
            "id": self.id,
            "titulo": self.titulo,
            "professor": self.professor,
            "disciplina": self.disciplina,
            "estado": self.estado.value,
            "ativa": self.esta_ativa(),
            "duracao_segundos": self.obter_duracao(),
            "total_registros": len(self.registros)
        }

    # ==========================================
    # Exportação dos dados
    # ==========================================

    def exportar(self):

        return {
            "id": self.id,
            "titulo": self.titulo,
            "professor": self.professor,
            "disciplina": self.disciplina,

            "estado": self.estado.value,

            "inicio": (
                self.inicio.isoformat()
                if self.inicio else None
            ),

            "fim": (
                self.fim.isoformat()
                if self.fim else None
            ),

            "duracao_segundos": self.obter_duracao(),

            "conteudo": self.obter_conteudo(),
            "atividades": self.obter_atividades(),
            "trabalhos": self.obter_trabalhos(),

            "registros": self.obter_registros(),

            "transcricao_completa": (
                self.obter_transcricao_completa()
            )
        }

    # ==========================================
    # Armazenamento local
    # ==========================================

    def salvar(self, diretorio=None):

        if self.id is None:
            raise RuntimeError(
                "Nenhuma aula foi iniciada."
            )

        if diretorio is None:

            diretorio = (
                Path(__file__).resolve().parent.parent
                / "dados"
                / "transcricoes"
            )

        diretorio = Path(diretorio)

        diretorio.mkdir(
            parents=True,
            exist_ok=True
        )

        arquivo = diretorio / f"{self.id}.json"

        temporario = diretorio / f"{self.id}.tmp"

        with temporario.open(
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.exportar(),
                f,
                ensure_ascii=False,
                indent=4
            )

        temporario.replace(arquivo)

        print(
            f"[Aula] Transcrição salva em: {arquivo}"
        )

        return arquivo