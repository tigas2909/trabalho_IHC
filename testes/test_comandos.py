import unittest

from robo.aula import Aula, EstadoAula
from robo.comandos import Comando, Comandos


class TestComandos(unittest.TestCase):

    def setUp(self):

        self.aula = Aula()

        self.comandos = Comandos(
            self.aula
        )

    def test_normalizar(self):

        resultado = self.comandos.normalizar(
            "  INÍCIO DA AULA!!!  "
        )

        self.assertEqual(
            resultado,
            "inicio da aula"
        )

    def test_identificar_inicio(self):

        comando = self.comandos.identificar(
            "Iniciar aula"
        )

        self.assertEqual(
            comando,
            Comando.INICIO
        )

    def test_identificar_atividade(self):

        comando = self.comandos.identificar(
            "Iniciar atividade!"
        )

        self.assertEqual(
            comando,
            Comando.ATIVIDADE
        )

    def test_identificar_trabalho(self):

        comando = self.comandos.identificar(
            "Iniciar trabalho"
        )

        self.assertEqual(
            comando,
            Comando.TRABALHO
        )

    def test_identificar_final(self):

        comando = self.comandos.identificar(
            "Finalizar aula."
        )

        self.assertEqual(
            comando,
            Comando.FINAL
        )

    def test_texto_normal(self):

        comando = self.comandos.identificar(
            "Vue utiliza componentes."
        )

        self.assertIsNone(comando)

    def test_evitar_ativacao_acidental(self):

        comando = self.comandos.identificar(
            "Vamos aprender a iniciar aula."
        )

        self.assertIsNone(comando)

    def test_executar_inicio(self):

        resultado = self.comandos.processar(
            "Iniciar aula"
        )

        self.assertTrue(
            resultado["resultado"]["sucesso"]
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.CONTEUDO
        )

    def test_executar_atividade(self):

        self.aula.iniciar()

        self.comandos.processar(
            "Iniciar atividade"
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.ATIVIDADE
        )

    def test_executar_trabalho(self):

        self.aula.iniciar()

        self.comandos.processar(
            "Iniciar trabalho"
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.TRABALHO
        )

    def test_executar_continuar(self):

        self.aula.iniciar()

        self.aula.iniciar_atividade()

        self.comandos.processar(
            "Continuar aula"
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.CONTEUDO
        )

    def test_executar_final(self):

        self.aula.iniciar()

        self.comandos.processar(
            "Finalizar aula"
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.FINALIZADO
        )

    def test_comando_invalido_no_estado(self):

        resultado = self.comandos.processar(
            "Iniciar atividade"
        )

        self.assertFalse(
            resultado["resultado"]["sucesso"]
        )

    def test_inicio_duplicado(self):

        self.aula.iniciar()

        resultado = self.comandos.processar(
            "Iniciar aula"
        )

        self.assertFalse(
            resultado["resultado"]["sucesso"]
        )

    def test_processar_transcricao(self):

        resultado = self.comandos.processar(
            "Hoje vamos estudar Python."
        )

        self.assertEqual(
            resultado["tipo"],
            "transcricao"
        )


if __name__ == "__main__":

    unittest.main()
    