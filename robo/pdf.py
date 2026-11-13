from pathlib import Path
from datetime import datetime
from uuid import UUID
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


class GeradorPDF:

    def __init__(self, diretorio=None):

        if diretorio is None:

            diretorio = (
                Path(__file__).resolve().parent.parent
                / "dados"
                / "relatorios"
            )

        self.diretorio = Path(diretorio)

        self.diretorio.mkdir(
            parents=True,
            exist_ok=True
        )

        self.estilos = self._criar_estilos()

    # ==========================================
    # Estilos do documento
    # ==========================================

    def _criar_estilos(self):

        estilos = getSampleStyleSheet()

        estilos.add(
            ParagraphStyle(
                name="TituloAula",
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=28,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#172554"),
                spaceAfter=18
            )
        )

        estilos.add(
            ParagraphStyle(
                name="SubtituloAula",
                fontName="Helvetica",
                fontSize=12,
                leading=17,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#475569"),
                spaceAfter=20
            )
        )

        estilos.add(
            ParagraphStyle(
                name="SecaoAula",
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=21,
                textColor=colors.HexColor("#1E3A8A"),
                spaceBefore=18,
                spaceAfter=10,
                keepWithNext=True
            )
        )

        estilos.add(
            ParagraphStyle(
                name="TextoAula",
                fontName="Helvetica",
                fontSize=12,
                leading=18,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#1F2937"),
                spaceAfter=8
            )
        )

        estilos.add(
            ParagraphStyle(
                name="ItemAula",
                fontName="Helvetica",
                fontSize=12,
                leading=18,
                leftIndent=16,
                firstLineIndent=-12,
                textColor=colors.HexColor("#1F2937"),
                spaceAfter=8
            )
        )

        estilos.add(
            ParagraphStyle(
                name="AvisoAula",
                fontName="Helvetica",
                fontSize=10,
                leading=15,
                textColor=colors.HexColor("#475569"),
                spaceBefore=15,
                spaceAfter=10
            )
        )

        return estilos

    # ==========================================
    # Tratamento de texto
    # ==========================================

    @staticmethod
    def _texto_seguro(texto):

        if texto is None:
            return ""

        texto = str(texto)

        return escape(texto).replace(
            "\n",
            "<br/>"
        )

    @staticmethod
    def _formatar_data(data):

        if not data:
            return "Não informada"

        try:

            data = datetime.fromisoformat(data)

            return data.strftime(
                "%d/%m/%Y às %H:%M"
            )

        except (ValueError, TypeError):

            return str(data)

    @staticmethod
    def _formatar_duracao(segundos):

        segundos = max(
            0,
            int(segundos or 0)
        )

        horas, restante = divmod(
            segundos,
            3600
        )

        minutos, segundos = divmod(
            restante,
            60
        )

        return (
            f"{horas:02d}h "
            f"{minutos:02d}min "
            f"{segundos:02d}s"
        )

    # ==========================================
    # Componentes do documento
    # ==========================================

    def _paragrafo(
        self,
        texto,
        estilo="TextoAula"
    ):

        return Paragraph(
            self._texto_seguro(texto),
            self.estilos[estilo]
        )

    def _secao(self, elementos, titulo):

        elementos.append(
            self._paragrafo(
                titulo,
                "SecaoAula"
            )
        )

    def _lista(self, elementos, itens):

        if not itens:

            elementos.append(
                self._paragrafo(
                    "Nenhuma informação registrada."
                )
            )

            return

        if isinstance(itens, str):

            itens = [itens]

        for item in itens:

            if isinstance(item, dict):

                texto = item.get(
                    "texto",
                    ""
                )

            else:

                texto = str(item)

            if not texto.strip():
                continue

            elementos.append(
                self._paragrafo(
                    f"• {texto}",
                    "ItemAula"
                )
            )

    # ==========================================
    # Identificação da aula
    # ==========================================

    def _identificacao(self, aula):

        dados = [

            [
                self._paragrafo("Disciplina"),
                self._paragrafo(
                    aula.get("disciplina")
                    or "Não informada"
                )
            ],

            [
                self._paragrafo("Professor"),
                self._paragrafo(
                    aula.get("professor")
                    or "Não informado"
                )
            ],

            [
                self._paragrafo("Início"),
                self._paragrafo(
                    self._formatar_data(
                        aula.get("inicio")
                    )
                )
            ],

            [
                self._paragrafo("Final"),
                self._paragrafo(
                    self._formatar_data(
                        aula.get("fim")
                    )
                )
            ],

            [
                self._paragrafo("Duração"),
                self._paragrafo(
                    self._formatar_duracao(
                        aula.get(
                            "duracao_segundos",
                            0
                        )
                    )
                )
            ]
        ]

        tabela = Table(
            dados,
            colWidths=[100, 360],
            hAlign="CENTER"
        )

        tabela.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E2E8F0")
                ),

                (
                    "ROWBACKGROUNDS",
                    (1, 0),
                    (1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC")
                    ]
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1")
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1")
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )

            ])
        )

        return tabela

    # ==========================================
    # Cabeçalho e rodapé
    # ==========================================

    @staticmethod
    def _pagina(canvas, documento):

        largura, altura = A4

        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#CBD5E1")
        )

        canvas.line(
            48,
            altura - 42,
            largura - 48,
            altura - 42
        )

        canvas.setFont(
            "Helvetica",
            9
        )

        canvas.setFillColor(
            colors.HexColor("#475569")
        )

        canvas.drawString(
            48,
            altura - 32,
            "Agente de Acessibilidade Educacional"
        )

        canvas.line(
            48,
            42,
            largura - 48,
            42
        )

        canvas.drawString(
            48,
            27,
            "Projeto IHC - IFPR"
        )

        canvas.drawRightString(
            largura - 48,
            27,
            f"Página {documento.page}"
        )

        canvas.restoreState()

    # ==========================================
    # Geração do PDF
    # ==========================================

    def gerar(self, aula, resumo=None):

        if not isinstance(aula, dict):

            raise TypeError(
                "Os dados da aula devem ser "
                "um dicionário."
            )

        if not aula.get("id"):

            raise ValueError(
                "A aula precisa possuir um ID."
            )

        if aula.get("estado") != "finalizado":

            raise ValueError(
                "A aula precisa estar finalizada."
            )

        if resumo is None:

            resumo = {}

        if not isinstance(resumo, dict):

            raise TypeError(
                "O resumo deve ser um dicionário."
            )

        aula_id = str(
            UUID(str(aula["id"]))
        )

        arquivo = (
            self.diretorio
            / f"resumo_{aula_id}.pdf"
        )

        temporario = arquivo.with_suffix(
            ".pdf.tmp"
        )

        titulo = (
            aula.get("titulo")
            or "Resumo da aula"
        )

        documento = SimpleDocTemplate(
            str(temporario),
            pagesize=A4,
            rightMargin=48,
            leftMargin=48,
            topMargin=60,
            bottomMargin=60,
            title=titulo,
            author=(
                "Agente de Acessibilidade "
                "Educacional - IFPR"
            ),
            subject="Material de estudo"
        )

        elementos = []

        # Título

        elementos.append(
            self._paragrafo(
                titulo,
                "TituloAula"
            )
        )

        elementos.append(
            self._paragrafo(
                "Material de estudo da aula",
                "SubtituloAula"
            )
        )

        # Identificação

        elementos.append(
            self._identificacao(aula)
        )

        elementos.append(
            Spacer(1, 18)
        )

        # Resumo geral

        self._secao(
            elementos,
            "1. Resumo geral"
        )

        if resumo.get("resumo_geral"):

            elementos.append(
                self._paragrafo(
                    resumo["resumo_geral"]
                )
            )

        else:

            elementos.append(
                self._paragrafo(
                    "Resumo automático ainda "
                    "não disponível."
                )
            )

        # Conceitos

        self._secao(
            elementos,
            "2. Principais conceitos"
        )

        self._lista(
            elementos,
            resumo.get("conceitos", [])
        )

        # Explicações

        self._secao(
            elementos,
            "3. Explicações importantes"
        )

        self._lista(
            elementos,
            resumo.get("explicacoes", [])
        )

        # Atividades

        self._secao(
            elementos,
            "4. Atividades solicitadas"
        )

        self._lista(
            elementos,
            resumo.get("atividades")
            or aula.get("atividades", [])
        )

        # Trabalhos

        self._secao(
            elementos,
            "5. Trabalhos solicitados"
        )

        self._lista(
            elementos,
            resumo.get("trabalhos")
            or aula.get("trabalhos", [])
        )

        # Prazos

        self._secao(
            elementos,
            "6. Prazos e requisitos"
        )

        self._lista(
            elementos,
            resumo.get("prazos", [])
        )

        # Revisão

        self._secao(
            elementos,
            "7. Pontos para revisão"
        )

        self._lista(
            elementos,
            resumo.get("revisao", [])
        )

        # Observações

        self._secao(
            elementos,
            "8. Observações"
        )

        elementos.append(
            self._paragrafo(
                resumo.get("observacoes")
                or "Nenhuma observação adicional."
            )
        )

        # Aviso

        elementos.append(
            self._paragrafo(
                "Este material é um apoio ao estudo. "
                "Resumos produzidos por inteligência "
                "artificial podem apresentar erros. "
                "Confirme informações importantes, "
                "atividades e prazos com o professor.",
                "AvisoAula"
            )
        )

        try:

            documento.build(
                elementos,
                onFirstPage=self._pagina,
                onLaterPages=self._pagina
            )

            temporario.replace(arquivo)

        finally:

            if temporario.exists():

                temporario.unlink()

        print(
            f"[PDF] Relatório gerado: {arquivo}"
        )

        return arquivo