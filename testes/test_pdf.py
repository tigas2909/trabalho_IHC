import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from robo.aula import Aula
from robo.pdf import GeradorPDF


class TestPDF(unittest.TestCase):

    def setUp(self):

        self.temporario = TemporaryDirectory()

        self.addCleanup(
            self.temporario.cleanup
        )

        self.gerador = GeradorPDF(
            diretorio=self.temporario.name
        )

        self.aula = Aula()

        self.aula.iniciar(
            titulo="Introdução à IHC",
            professor="Marcos",
            disciplina="IHC"
        )

        self.aula.registrar(
            "IHC estuda a interação entre "
            "pessoas e computadores."
        )

        self.aula.iniciar_atividade()

        self.aula.registrar(
            "Analisar uma interface."
        )

        self.aula.iniciar_trabalho()

        self.aula.registrar(
            "Desenvolver uma interface acessível."
        )

        self.dados = self.aula.finalizar()

        self.resumo = {

            "resumo_geral": (
                "A aula apresentou conceitos "
                "de IHC e acessibilidade."
            ),

            "conceitos": [
                "Usabilidade",
                "Acessibilidade"
            ],

            "explicacoes": [
                "Interfaces devem considerar "
                "as necessidades dos usuários."
            ],

            "atividades": [
                "Analisar uma interface."
            ],

            "trabalhos": [
                "Desenvolver uma interface."
            ],

            "prazos": [
                "Entrega na próxima semana."
            ],

            "revisao": [
                "Revisar conceitos de IHC."
            ],

            "observacoes": (
                "Material gerado para teste."
            )
        }

    def test_gerar_pdf(self):

        arquivo = self.gerador.gerar(
            self.dados,
            self.resumo
        )

        self.assertTrue(
            arquivo.exists()
        )

        self.assertEqual(
            arquivo.suffix,
            ".pdf"
        )

    def test_pdf_valido(self):

        arquivo = self.gerador.gerar(
            self.dados,
            self.resumo
        )

        with arquivo.open("rb") as f:

            assinatura = f.read(5)

        self.assertEqual(
            assinatura,
            b"%PDF-"
        )

    def test_pdf_sem_resumo(self):

        arquivo = self.gerador.gerar(
            self.dados
        )

        self.assertTrue(
            arquivo.exists()
        )

    def test_aula_sem_id(self):

        with self.assertRaises(ValueError):

            self.gerador.gerar({})

    def test_dados_invalidos(self):

        with self.assertRaises(TypeError):

            self.gerador.gerar(
                "Dados inválidos"
            )

    def test_resumo_invalido(self):

        with self.assertRaises(TypeError):

            self.gerador.gerar(
                self.dados,
                "Resumo inválido"
            )

    def test_criar_diretorio(self):

        diretorio = (
            Path(self.temporario.name)
            / "relatorios"
        )

        gerador = GeradorPDF(
            diretorio=diretorio
        )

        self.assertTrue(
            gerador.diretorio.exists()
        )

    def test_caracteres_especiais(self):

        resumo = self.resumo.copy()

        resumo["resumo_geral"] = (
            "Em HTML, utilizamos <div> "
            "e operadores como 5 > 3 "
            "e A & B."
        )

        arquivo = self.gerador.gerar(
            self.dados,
            resumo
        )

        self.assertTrue(
            arquivo.exists()
        )

    def test_resumo_extenso(self):

        resumo = self.resumo.copy()

        resumo["explicacoes"] = [

            (
                f"Conceito número {i}: "
                "Interfaces acessíveis permitem "
                "que diferentes usuários tenham "
                "acesso ao conteúdo educacional."
            )

            for i in range(200)
        ]

        arquivo = self.gerador.gerar(
            self.dados,
            resumo
        )

        self.assertTrue(
            arquivo.exists()
        )

    def test_rejeitar_aula_nao_finalizada(self):

        aula = Aula()

        aula.iniciar()

        with self.assertRaises(ValueError):

            self.gerador.gerar(
                aula.exportar()
            )


if __name__ == "__main__":

    unittest.main()