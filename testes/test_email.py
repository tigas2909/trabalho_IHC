import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from robo.email import EnviadorEmail


class TestEmail(unittest.TestCase):

    def setUp(self):

        self.temporario = TemporaryDirectory()

        self.addCleanup(
            self.temporario.cleanup
        )

        self.arquivo = (
            Path(self.temporario.name)
            / "resumo.pdf"
        )

        # Assinatura utilizada para testar
        # a validação básica do arquivo.

        self.arquivo.write_bytes(
            b"%PDF-1.4\nTeste de PDF"
        )

        self.enviador = EnviadorEmail(
            host="smtp.example.com",
            porta=587,
            usuario="teste@example.com",
            senha="senha_de_teste",
            nome="Agente IHC"
        )

        self.aula = {
            "titulo": "Introdução à IHC",
            "disciplina": "IHC",
            "professor": "Marcos",
            "inicio": (
                "2026-11-12T19:00:00-03:00"
            )
        }

    def test_configuracao_valida(self):

        self.assertTrue(
            self.enviador.validar_configuracao()
        )

    def test_configuracao_sem_senha(self):

        self.enviador.senha = None

        with self.assertRaises(ValueError):

            self.enviador.validar_configuracao()

    def test_email_valido(self):

        self.assertTrue(
            self.enviador.validar_email(
                "aluno@example.com"
            )
        )

    def test_email_invalido(self):

        self.assertFalse(
            self.enviador.validar_email(
                "email-invalido"
            )
        )

    def test_destinatario_unico(self):

        resultado = (
            self.enviador.normalizar_destinatarios(
                "aluno@example.com"
            )
        )

        self.assertEqual(
            resultado,
            ["aluno@example.com"]
        )

    def test_remover_destinatarios_duplicados(self):

        resultado = (
            self.enviador.normalizar_destinatarios(
                [
                    "aluno@example.com",
                    "aluno@example.com"
                ]
            )
        )

        self.assertEqual(
            len(resultado),
            1
        )

    def test_sem_destinatarios(self):

        with self.assertRaises(ValueError):

            self.enviador.normalizar_destinatarios(
                []
            )

    def test_pdf_existente(self):

        resultado = (
            self.enviador.validar_pdf(
                self.arquivo
            )
        )

        self.assertEqual(
            resultado,
            self.arquivo
        )

    def test_pdf_inexistente(self):

        with self.assertRaises(
            FileNotFoundError
        ):

            self.enviador.validar_pdf(
                "arquivo-inexistente.pdf"
            )

    def test_arquivo_invalido(self):

        arquivo = (
            Path(self.temporario.name)
            / "invalido.pdf"
        )

        arquivo.write_text(
            "Não é um PDF"
        )

        with self.assertRaises(ValueError):

            self.enviador.validar_pdf(
                arquivo
            )

    def test_criar_mensagem(self):

        mensagem = (
            self.enviador.criar_mensagem(
                "aluno@example.com",
                self.arquivo,
                self.aula
            )
        )

        self.assertEqual(
            mensagem["To"],
            "aluno@example.com"
        )

        self.assertIn(
            "Introdução à IHC",
            mensagem["Subject"]
        )

    def test_anexo_pdf(self):

        mensagem = (
            self.enviador.criar_mensagem(
                "aluno@example.com",
                self.arquivo,
                self.aula
            )
        )

        anexos = list(
            mensagem.iter_attachments()
        )

        self.assertEqual(
            len(anexos),
            1
        )

        self.assertEqual(
            anexos[0].get_filename(),
            "resumo.pdf"
        )

        self.assertEqual(
            anexos[0].get_content_type(),
            "application/pdf"
        )

    @patch("robo.email.smtplib.SMTP")
    def test_enviar_email(self, smtp_mock):

        servidor = MagicMock()

        smtp_mock.return_value = servidor

        resultado = self.enviador.enviar(
            destinatarios="aluno@example.com",
            arquivo=self.arquivo,
            aula=self.aula
        )

        self.assertTrue(
            resultado["sucesso"]
        )

        self.assertEqual(
            resultado["total_enviados"],
            1
        )

        servidor.starttls.assert_called_once()

        servidor.login.assert_called_once()

        servidor.send_message.assert_called_once()

        servidor.quit.assert_called_once()

    @patch("robo.email.smtplib.SMTP")
    def test_enviar_multiplos(self, smtp_mock):

        servidor = MagicMock()

        smtp_mock.return_value = servidor

        resultado = self.enviador.enviar(
            destinatarios=[
                "aluno1@example.com",
                "aluno2@example.com"
            ],
            arquivo=self.arquivo,
            aula=self.aula
        )

        self.assertTrue(
            resultado["sucesso"]
        )

        self.assertEqual(
            resultado["total_enviados"],
            2
        )

        self.assertEqual(
            servidor.send_message.call_count,
            2
        )

    @patch("robo.email.smtplib.SMTP")
    def test_falha_conexao(self, smtp_mock):

        smtp_mock.side_effect = (
            ConnectionError(
                "Falha simulada"
            )
        )

        resultado = self.enviador.enviar(
            destinatarios="aluno@example.com",
            arquivo=self.arquivo,
            aula=self.aula
        )

        self.assertFalse(
            resultado["sucesso"]
        )

        self.assertEqual(
            resultado["total_falhas"],
            1
        )

    @patch("robo.email.smtplib.SMTP")
    def test_falha_parcial(self, smtp_mock):

        servidor = MagicMock()

        smtp_mock.return_value = servidor

        servidor.send_message.side_effect = [
            {},
            RuntimeError("Falha simulada")
        ]

        resultado = self.enviador.enviar(
            destinatarios=[
                "aluno1@example.com",
                "aluno2@example.com"
            ],
            arquivo=self.arquivo,
            aula=self.aula
        )

        self.assertFalse(
            resultado["sucesso"]
        )

        self.assertEqual(
            resultado["total_enviados"],
            1
        )

        self.assertEqual(
            resultado["total_falhas"],
            1
        )


if __name__ == "__main__":

    unittest.main()