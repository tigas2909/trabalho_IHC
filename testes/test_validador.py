import json
import unittest

from copy import deepcopy
from datetime import datetime

from robo.aula import Aula

from robo.validador import (
    ValidadorResumo,
    ErroValidacaoResumo
)


class TestValidador(unittest.TestCase):

    def setUp(self):

        self.validador = ValidadorResumo()

        aula = Aula()

        aula.iniciar(
            titulo="Introdução à IHC",
            professor="Marcos",
            disciplina="IHC"
        )

        aula.registrar(
            "Usabilidade é um conceito "
            "importante para IHC."
        )

        self.aula = aula.finalizar()

        self.resumo = {

            "versao_esquema": "1.0",

            "identificacao": {

                "aula_id": self.aula["id"],

                "titulo": self.aula["titulo"],

                "disciplina": self.aula["disciplina"],

                "professor": self.aula["professor"],

                "data": datetime.fromisoformat(
                    self.aula["inicio"]
                ).date().isoformat(),

                "inicio": self.aula["inicio"],

                "fim": self.aula["fim"],

                "duracao_segundos": (
                    self.aula["duracao_segundos"]
                ),

                "idioma": "pt-BR"
            },

            "resumo": {

                "resumo_geral": (
                    "A aula apresentou usabilidade."
                ),

                "objetivos_da_aula": [],

                "assuntos_principais": [
                    "Usabilidade"
                ],

                "palavras_chave": [
                    "IHC",
                    "Usabilidade"
                ],

                "nivel_de_dificuldade": None
            },

            "conteudo": {

                "topicos": [],

                "conceitos": [

                    {
                        "id": "conceito_01",

                        "nome": "Usabilidade",

                        "definicao": "",

                        "explicacao": (
                            "Conceito importante "
                            "para IHC."
                        ),

                        "exemplo": None,

                        "aplicacao_pratica": None,

                        "referencias_transcricao": [
                            1
                        ]
                    }
                ],

                "exemplos": [],

                "formulas": [],

                "codigos": [],

                "procedimentos": []
            },

            "atividades": [],

            "trabalhos": [],

            "avaliacoes": [],

            "prazos": [],

            "materiais_complementares": [],

            "revisao": {

                "pontos_principais": [],

                "conceitos_fundamentais": [],

                "perguntas_e_respostas": [],

                "exercicios_de_fixacao": [],

                "flashcards": [],

                "sugestao_de_estudo": []
            },

            "acessibilidade": {

                "termos_tecnicos": [],

                "referencias_visuais": [],

                "trechos_incompletos": [],

                "adaptacoes_textuais": [],

                "informacoes_que_precisam_de_confirmacao": []
            },

            "observacoes": {

                "avisos_do_professor": [],

                "informacoes_adicionais": [],

                "contradicoes_identificadas": [],

                "limitacoes_da_transcricao": [],

                "informacoes_nao_confirmadas": []
            },

            "qualidade_do_processamento": {

                "conteudo_suficiente": True,

                "total_registros_analisados": 1,

                "total_registros_utilizados": 1,

                "registros_incompletos": [],

                "campos_sem_informacao": [],

                "necessita_revisao_humana": False,

                "motivos_para_revisao": []
            }
        }

    # ==========================================
    # Resumo válido
    # ==========================================

    def test_resumo_valido(self):

        self.assertTrue(
            self.validador.validar(
                self.resumo,
                self.aula
            )
        )

    # ==========================================
    # Campos obrigatórios
    # ==========================================

    def test_campo_obrigatorio_ausente(self):

        del self.resumo["conteudo"]

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Campos extras
    # ==========================================

    def test_campo_extra(self):

        self.resumo["campo_inventado"] = True

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Tipos inválidos
    # ==========================================

    def test_tipo_invalido(self):

        self.resumo["atividades"] = (
            "Atividade inválida"
        )

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Referências inexistentes
    # ==========================================

    def test_referencia_inexistente(self):

        self.resumo["conteudo"][
            "conceitos"
        ][0][
            "referencias_transcricao"
        ] = [999]

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo,
                self.aula
            )

    # ==========================================
    # Identificadores duplicados
    # ==========================================

    def test_identificador_duplicado(self):

        conceito = deepcopy(
            self.resumo["conteudo"][
                "conceitos"
            ][0]
        )

        self.resumo["conteudo"][
            "conceitos"
        ].append(conceito)

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Identificação da aula
    # ==========================================

    def test_identificacao_incorreta(self):

        self.resumo["identificacao"][
            "professor"
        ] = "Outro professor"

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo,
                self.aula
            )

    # ==========================================
    # Datas inválidas
    # ==========================================

    def test_data_invalida(self):

        self.resumo["identificacao"][
            "data"
        ] = "2026-99-99"

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Enumerações inválidas
    # ==========================================

    def test_enumeracao_invalida(self):

        self.resumo["resumo"][
            "nivel_de_dificuldade"
        ] = "impossivel"

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Conversão de JSON válido
    # ==========================================

    def test_json_valido(self):

        resposta = json.dumps(
            self.resumo
        )

        resultado = (
            self.validador.validar_json(
                resposta,
                self.aula
            )
        )

        self.assertEqual(
            resultado,
            self.resumo
        )

    # ==========================================
    # JSON inválido
    # ==========================================

    def test_json_invalido(self):

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar_json(
                '{"resumo":'
            )

    # ==========================================
    # Contagem de registros
    # ==========================================

    def test_contagem_invalida(self):

        self.resumo[
            "qualidade_do_processamento"
        ][
            "total_registros_utilizados"
        ] = 50

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo,
                self.aula
            )

    # ==========================================
    # Relação entre prazo e trabalho
    # ==========================================

    def test_prazo_sem_referencia_valida(self):

        self.resumo["prazos"].append({

            "id": "prazo_01",

            "titulo": "Entrega do trabalho",

            "tipo": "trabalho",

            "referencia_id": "trabalho_999",

            "descricao_original": (
                "Entregar na próxima semana."
            ),

            "data": None,

            "horario": None,

            "confirmado": False,

            "observacoes": []
        })

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo
            )

    # ==========================================
    # Registros incompletos
    # ==========================================

    def test_registro_incompleto_inexistente(self):

        self.resumo[
            "qualidade_do_processamento"
        ][
            "registros_incompletos"
        ] = [500]

        with self.assertRaises(
            ErroValidacaoResumo
        ):

            self.validador.validar(
                self.resumo,
                self.aula
            )


if __name__ == "__main__":

    unittest.main()