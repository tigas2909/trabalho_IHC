import json

from pathlib import Path
from datetime import datetime

from jsonschema import (
    Draft202012Validator,
    FormatChecker
)


class ErroValidacaoResumo(ValueError):

    def __init__(self, erros):

        self.erros = erros

        mensagem = (
            "O resumo possui erros de validação:\n"
            + "\n".join(
                f"- {erro}"
                for erro in erros
            )
        )

        super().__init__(mensagem)


class ValidadorResumo:

    def __init__(self, arquivo=None):

        if arquivo is None:

            arquivo = (
                Path(__file__).resolve().parent
                / "esquema_resumo.json"
            )

        self.arquivo = Path(arquivo)

        if not self.arquivo.is_file():

            raise FileNotFoundError(
                f"JSON Schema não encontrado: "
                f"{self.arquivo}"
            )

        with self.arquivo.open(
            "r",
            encoding="utf-8"
        ) as f:

            self.esquema = json.load(f)

        Draft202012Validator.check_schema(
            self.esquema
        )

        self.validador = Draft202012Validator(
            self.esquema,
            format_checker=FormatChecker()
        )

    # ==========================================
    # Validação estrutural
    # ==========================================

    def validar_estrutura(self, resumo):

        erros = []

        for erro in self.validador.iter_errors(
            resumo
        ):

            caminho = ".".join(
                str(item)
                for item in erro.absolute_path
            )

            if not caminho:
                caminho = "raiz"

            erros.append(
                f"{caminho}: {erro.message}"
            )

        return erros

    # ==========================================
    # Percorrer estruturas JSON
    # ==========================================

    def percorrer(self, dados, caminho=""):

        if isinstance(dados, dict):

            yield caminho, dados

            for chave, valor in dados.items():

                novo_caminho = (
                    f"{caminho}.{chave}"
                    if caminho
                    else chave
                )

                yield from self.percorrer(
                    valor,
                    novo_caminho
                )

        elif isinstance(dados, list):

            for indice, valor in enumerate(dados):

                novo_caminho = (
                    f"{caminho}[{indice}]"
                )

                yield from self.percorrer(
                    valor,
                    novo_caminho
                )

    # ==========================================
    # Identificadores únicos
    # ==========================================

    def validar_identificadores(self, resumo):

        erros = []

        identificadores = {}

        for caminho, objeto in self.percorrer(
            resumo
        ):

            identificador = objeto.get("id")

            if identificador is None:
                continue

            if identificador in identificadores:

                erros.append(
                    f"ID duplicado: {identificador}. "
                    f"Encontrado em {caminho} e "
                    f"{identificadores[identificador]}."
                )

            else:

                identificadores[
                    identificador
                ] = caminho

        return erros

    # ==========================================
    # Referências à transcrição
    # ==========================================

    def validar_referencias(
        self,
        resumo,
        aula
    ):

        erros = []

        registros = aula.get(
            "registros",
            []
        )

        ids_validos = {
            registro["id"]
            for registro in registros
            if "id" in registro
        }

        for caminho, objeto in self.percorrer(
            resumo
        ):

            referencias = objeto.get(
                "referencias_transcricao",
                []
            )

            for identificador in referencias:

                if identificador not in ids_validos:

                    erros.append(
                        f"{caminho}: registro "
                        f"{identificador} não existe "
                        "na transcrição original."
                    )

        incompletos = resumo[
            "qualidade_do_processamento"
        ]["registros_incompletos"]

        for identificador in incompletos:

            if identificador not in ids_validos:

                erros.append(
                    "Registro incompleto inexistente: "
                    f"{identificador}."
                )

        return erros

    # ==========================================
    # Identificação da aula
    # ==========================================

    def validar_identificacao(
        self,
        resumo,
        aula
    ):

        erros = []

        identificacao = resumo["identificacao"]

        correspondencias = {
            "aula_id": "id",
            "titulo": "titulo",
            "professor": "professor",
            "disciplina": "disciplina",
            "inicio": "inicio",
            "fim": "fim",
            "duracao_segundos": (
                "duracao_segundos"
            )
        }

        for campo, origem in (
            correspondencias.items()
        ):

            esperado = aula.get(origem)

            recebido = identificacao.get(campo)

            if recebido != esperado:

                erros.append(
                    f"identificacao.{campo}: "
                    "valor diferente dos dados "
                    "originais da aula."
                )

        inicio = aula.get("inicio")

        if inicio:

            data_esperada = datetime.fromisoformat(
                inicio
            ).date().isoformat()

        else:

            data_esperada = None

        if identificacao["data"] != data_esperada:

            erros.append(
                "identificacao.data: "
                "data diferente da aula original."
            )

        return erros

    # ==========================================
    # Relações dos prazos
    # ==========================================

    def validar_prazos(self, resumo):

        erros = []

        categorias = {

            "atividade": {
                item["id"]: item
                for item in resumo["atividades"]
            },

            "trabalho": {
                item["id"]: item
                for item in resumo["trabalhos"]
            },

            "avaliacao": {
                item["id"]: item
                for item in resumo["avaliacoes"]
            }
        }

        for prazo in resumo["prazos"]:

            tipo = prazo["tipo"]

            referencia_id = prazo["referencia_id"]

            if referencia_id is None:
                continue

            if tipo not in categorias:

                erros.append(
                    f"Prazo {prazo['id']}: "
                    "tipo incompatível com "
                    "a referência informada."
                )

                continue

            entidade = categorias[tipo].get(
                referencia_id
            )

            if entidade is None:

                erros.append(
                    f"Prazo {prazo['id']}: "
                    f"referência {referencia_id} "
                    "não encontrada na categoria "
                    f"{tipo}."
                )

                continue

            if tipo in (
                "atividade",
                "trabalho"
            ):

                prazo_original = entidade["prazo"]

            else:

                prazo_original = entidade

            for campo in (
                "data",
                "horario"
            ):

                valor_original = (
                    prazo_original.get(campo)
                )

                valor_prazo = prazo.get(campo)

                if (
                    valor_original is not None
                    and valor_prazo is not None
                    and valor_original != valor_prazo
                ):

                    erros.append(
                        f"Prazo {prazo['id']}: "
                        f"{campo} contraditório "
                        "em relação à entidade "
                        f"{referencia_id}."
                    )

        return erros

    # ==========================================
    # Validação das contagens
    # ==========================================

    def validar_contagens(
        self,
        resumo,
        aula
    ):

        erros = []

        qualidade = resumo[
            "qualidade_do_processamento"
        ]

        total_registros = len(
            aula.get("registros", [])
        )

        analisados = qualidade[
            "total_registros_analisados"
        ]

        utilizados = qualidade[
            "total_registros_utilizados"
        ]

        ids_utilizados = set()

        for _, objeto in self.percorrer(resumo):

            ids_utilizados.update(
                objeto.get(
                    "referencias_transcricao",
                    []
                )
            )

        if (
            analisados is not None
            and analisados > total_registros
        ):

            erros.append(
                "Quantidade de registros analisados "
                "superior à quantidade original."
            )

        if (
            utilizados is not None
            and utilizados != len(ids_utilizados)
        ):

            erros.append(
                "Quantidade de registros utilizados "
                "não corresponde às referências "
                "distintas do resumo."
            )

        if (
            analisados is not None
            and len(ids_utilizados) > analisados
        ):

            erros.append(
                "Existem mais registros utilizados "
                "do que registros analisados."
            )

        return erros

    # ==========================================
    # Validação completa
    # ==========================================

    def validar(self, resumo, aula=None):

        erros = self.validar_estrutura(
            resumo
        )

        # A estrutura precisa ser válida antes
        # das verificações semânticas.

        if erros:

            raise ErroValidacaoResumo(erros)

        erros.extend(
            self.validar_identificadores(
                resumo
            )
        )

        erros.extend(
            self.validar_prazos(
                resumo
            )
        )

        if aula is not None:

            erros.extend(
                self.validar_identificacao(
                    resumo,
                    aula
                )
            )

            erros.extend(
                self.validar_referencias(
                    resumo,
                    aula
                )
            )

            erros.extend(
                self.validar_contagens(
                    resumo,
                    aula
                )
            )

        if erros:

            raise ErroValidacaoResumo(erros)

        print(
            "[Validador] Resumo aprovado."
        )

        return True

    # ==========================================
    # Converter e validar resposta JSON
    # ==========================================

    def validar_json(
        self,
        resposta,
        aula=None
    ):

        if not isinstance(resposta, str):

            raise TypeError(
                "A resposta deve ser uma string."
            )

        try:

            resumo = json.loads(resposta)

        except json.JSONDecodeError as erro:

            raise ErroValidacaoResumo([
                "Resposta JSON inválida: "
                f"{erro.msg}, linha {erro.lineno}, "
                f"coluna {erro.colno}."
            ]) from erro

        self.validar(
            resumo,
            aula
        )

        return resumo