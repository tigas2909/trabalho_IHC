import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from robo.agente import Agente
from robo.aula import EstadoAula


class TestAgente(unittest.TestCase):

    def setUp(self):

        self.temporario = TemporaryDirectory()

        self.addCleanup(
            self.temporario.cleanup
        )

        self.agente = Agente(
            diretorio=self.temporario.name
        )

        self.eventos = []

        self.agente.adicionar_ouvinte(
            self.eventos.append
        )

    def test_estado_inicial(self):

        self.assertEqual(
            self.agente.aula.estado,
            EstadoAula.AGUARDANDO
        )

    def test_iniciar_por_comando(self):

        resultado = (
            self.agente.processar_transcricao(
                "Iniciar aula"
            )
        )

        self.assertTrue(
            resultado["sucesso"]
        )

        self.assertTrue(
            self.agente.aula.esta_ativa()
        )

    def test_iniciar_manualmente(self):

        resultado = self.agente.iniciar_aula(
            titulo="Introdução à IHC",
            professor="Marcos",
            disciplina="IHC"
        )

        self.assertEqual(
            resultado["titulo"],
            "Introdução à IHC"
        )

    def test_registrar_legenda(self):

        self.agente.iniciar_aula()

        resultado = (
            self.agente.processar_transcricao(
                "IHC estuda a interação entre "
                "pessoas e computadores."
            )
        )

        self.assertEqual(
            resultado["tipo"],
            "legenda"
        )

        self.assertEqual(
            len(self.agente.aula.registros),
            1
        )

    def test_ignorar_fora_da_aula(self):

        resultado = (
            self.agente.processar_transcricao(
                "Teste de áudio."
            )
        )

        self.assertEqual(
            resultado["tipo"],
            "ignorado"
        )

    def test_ignorar_texto_vazio(self):

        resultado = (
            self.agente.processar_transcricao(
                "    "
            )
        )

        self.assertEqual(
            resultado["tipo"],
            "ignorado"
        )

    def test_registrar_atividade(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Iniciar atividade"
        )

        self.agente.processar_transcricao(
            "Façam uma análise de usabilidade."
        )

        self.assertEqual(
            len(
                self.agente.aula.obter_atividades()
            ),
            1
        )

    def test_registrar_trabalho(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Iniciar trabalho"
        )

        self.agente.processar_transcricao(
            "Criem uma interface acessível."
        )

        self.assertEqual(
            len(
                self.agente.aula.obter_trabalhos()
            ),
            1
        )

    def test_finalizar_e_salvar(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Conteúdo de teste."
        )

        resultado = (
            self.agente.finalizar_aula()
        )

        self.assertTrue(
            resultado["sucesso"]
        )

        self.assertEqual(
            resultado["tipo"],
            "finalizacao"
        )

        arquivo = Path(
            resultado["arquivo"]
        )

        self.assertTrue(
            arquivo.exists()
        )

    def test_evento_de_legenda(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Uma legenda de teste."
        )

        tipos = [
            evento["tipo"]
            for evento in self.eventos
        ]

        self.assertIn(
            "legenda",
            tipos
        )

    def test_evento_resumo_pendente(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Conteúdo educacional."
        )

        self.agente.finalizar_aula()

        tipos = [
            evento["tipo"]
            for evento in self.eventos
        ]

        self.assertIn(
            "resumo_pendente",
            tipos
        )

    def test_comando_rejeitado(self):

        resultado = (
            self.agente.processar_transcricao(
                "Iniciar atividade"
            )
        )

        self.assertFalse(
            resultado["sucesso"]
        )

    def test_obter_status(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Teste de status."
        )

        status = self.agente.obter_status()

        self.assertEqual(
            status["ultima_legenda"],
            "Teste de status."
        )

    def test_salvar_progresso(self):

        self.agente.iniciar_aula()

        self.agente.processar_transcricao(
            "Conteúdo parcial."
        )

        arquivo = (
            self.agente.salvar_progresso()
        )

        self.assertTrue(
            arquivo.exists()
        )

    def test_remover_ouvinte(self):

        eventos = []

        callback = eventos.append

        self.agente.adicionar_ouvinte(
            callback
        )

        self.agente.remover_ouvinte(
            callback
        )

        self.agente.iniciar_aula()

        self.assertEqual(
            len(eventos),
            0
        )


if __name__ == "__main__":
    unittest.main()