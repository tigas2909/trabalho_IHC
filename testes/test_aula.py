import unittest

from tempfile import TemporaryDirectory

from robo.aula import Aula, EstadoAula


class TestAula(unittest.TestCase):

    def setUp(self):

        self.aula = Aula()

    def test_estado_inicial(self):

        self.assertEqual(
            self.aula.estado,
            EstadoAula.AGUARDANDO
        )

    def test_iniciar_aula(self):

        self.aula.iniciar(
            titulo="Introdução ao Vue",
            professor="Marcos",
            disciplina="Desenvolvimento Web"
        )

        self.assertTrue(
            self.aula.esta_ativa()
        )

        self.assertEqual(
            self.aula.estado,
            EstadoAula.CONTEUDO
        )

    def test_registrar_conteudo(self):

        self.aula.iniciar()

        self.aula.registrar(
            "Vue é um framework JavaScript."
        )

        self.assertEqual(
            len(self.aula.obter_conteudo()),
            1
        )

    def test_registrar_atividade(self):

        self.aula.iniciar()

        self.aula.iniciar_atividade()

        self.aula.registrar(
            "Criem um componente Vue."
        )

        self.assertEqual(
            len(self.aula.obter_atividades()),
            1
        )

    def test_registrar_trabalho(self):

        self.aula.iniciar()

        self.aula.iniciar_trabalho()

        self.aula.registrar(
            "Entregar um projeto na próxima semana."
        )

        self.assertEqual(
            len(self.aula.obter_trabalhos()),
            1
        )

    def test_continuar_aula(self):

        self.aula.iniciar()

        self.aula.iniciar_atividade()

        self.aula.continuar_aula()

        self.assertEqual(
            self.aula.estado,
            EstadoAula.CONTEUDO
        )

    def test_finalizar_aula(self):

        self.aula.iniciar()

        dados = self.aula.finalizar()

        self.assertEqual(
            self.aula.estado,
            EstadoAula.FINALIZADO
        )

        self.assertFalse(
            self.aula.esta_ativa()
        )

        self.assertIsNotNone(
            dados["fim"]
        )

    def test_registro_fora_da_aula(self):

        registro = self.aula.registrar(
            "Texto fora da aula."
        )

        self.assertIsNone(registro)

        self.assertEqual(
            len(self.aula.registros),
            0
        )

    def test_salvar_aula(self):

        self.aula.iniciar()

        self.aula.registrar(
            "Teste de armazenamento."
        )

        self.aula.finalizar()

        with TemporaryDirectory() as diretorio:

            arquivo = self.aula.salvar(diretorio)

            self.assertTrue(
                arquivo.exists()
            )

    def test_impedir_inicio_duplicado(self):

        self.aula.iniciar()

        with self.assertRaises(RuntimeError):

            self.aula.iniciar()


if __name__ == "__main__":

    unittest.main()