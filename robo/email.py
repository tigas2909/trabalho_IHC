import os
import ssl
import smtplib

from pathlib import Path
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class EnviadorEmail:

    def __init__(
        self,
        host=None,
        porta=None,
        usuario=None,
        senha=None,
        nome=None,
        timeout=None
    ):

        self.host = (
            host
            or os.getenv(
                "SMTP_HOST",
                "smtp.gmail.com"
            )
        )

        self.porta = int(
            porta
            or os.getenv("SMTP_PORT", "587")
        )

        self.usuario = (
            usuario
            or os.getenv("SMTP_USER")
        )

        self.senha = (
            senha
            or os.getenv("SMTP_PASSWORD")
        )

        self.nome = (
            nome
            or os.getenv(
                "SMTP_NOME",
                "Agente de Acessibilidade Educacional"
            )
        )

        self.timeout = int(
            timeout
            or os.getenv("SMTP_TIMEOUT", "30")
        )

    # ==========================================
    # Validação das configurações
    # ==========================================

    def validar_configuracao(self):

        if not self.usuario:

            raise ValueError(
                "SMTP_USER não configurado."
            )

        if not self.senha:

            raise ValueError(
                "SMTP_PASSWORD não configurado."
            )

        if not self.host:

            raise ValueError(
                "Servidor SMTP não configurado."
            )

        if self.porta not in (465, 587):

            raise ValueError(
                "Utilize a porta SMTP 465 ou 587."
            )

        return True

    # ==========================================
    # Validação dos destinatários
    # ==========================================

    @staticmethod
    def validar_email(endereco):

        if not isinstance(endereco, str):

            return False

        endereco = endereco.strip()

        if "\n" in endereco or "\r" in endereco:

            return False

        _, email = parseaddr(endereco)

        if email != endereco:

            return False

        if email.count("@") != 1:

            return False

        usuario, dominio = email.split("@")

        if not usuario or not dominio:

            return False

        if "." not in dominio:

            return False

        if any(
            caractere.isspace()
            for caractere in email
        ):

            return False

        return True

    def normalizar_destinatarios(
        self,
        destinatarios
    ):

        if isinstance(destinatarios, str):

            destinatarios = [destinatarios]

        if not isinstance(
            destinatarios,
            (list, tuple, set)
        ):

            raise TypeError(
                "Os destinatários devem ser "
                "um e-mail ou uma coleção de e-mails."
            )

        resultado = []

        for endereco in destinatarios:

            if not self.validar_email(endereco):

                raise ValueError(
                    "Endereço de e-mail inválido."
                )

            endereco = endereco.strip()

            if endereco not in resultado:

                resultado.append(endereco)

        if not resultado:

            raise ValueError(
                "Nenhum destinatário informado."
            )

        return resultado

    # ==========================================
    # Validação do PDF
    # ==========================================

    @staticmethod
    def validar_pdf(arquivo):

        arquivo = Path(arquivo)

        if not arquivo.is_file():

            raise FileNotFoundError(
                f"PDF não encontrado: {arquivo}"
            )

        if arquivo.suffix.lower() != ".pdf":

            raise ValueError(
                "O arquivo precisa ser um PDF."
            )

        with arquivo.open("rb") as f:

            assinatura = f.read(5)

        if assinatura != b"%PDF-":

            raise ValueError(
                "O arquivo não possui uma "
                "assinatura PDF válida."
            )

        return arquivo

    # ==========================================
    # Formatação dos dados
    # ==========================================

    @staticmethod
    def formatar_data(data):

        if not data:

            return "Não informada"

        try:

            return datetime.fromisoformat(
                data
            ).strftime(
                "%d/%m/%Y às %H:%M"
            )

        except (ValueError, TypeError):

            return str(data)

    # ==========================================
    # Construção da mensagem
    # ==========================================

    def criar_mensagem(
        self,
        destinatario,
        arquivo,
        aula
    ):

        if not isinstance(aula, dict):

            raise TypeError(
                "Os dados da aula devem ser "
                "um dicionário."
            )

        if not self.validar_email(destinatario):

            raise ValueError(
                "Destinatário inválido."
            )

        arquivo = self.validar_pdf(arquivo)

        titulo = (
            aula.get("titulo")
            or "Aula"
        )

        disciplina = (
            aula.get("disciplina")
            or "Não informada"
        )

        professor = (
            aula.get("professor")
            or "Não informado"
        )

        data = self.formatar_data(
            aula.get("inicio")
        )

        # Evita que quebras de linha sejam
        # utilizadas no cabeçalho do e-mail.

        titulo_assunto = (
            str(titulo)
            .replace("\r", " ")
            .replace("\n", " ")
        )

        mensagem = EmailMessage()

        mensagem["From"] = formataddr(
            (
                self.nome,
                self.usuario
            )
        )

        mensagem["To"] = destinatario

        mensagem["Subject"] = (
            f"Resumo da aula - {titulo_assunto}"
        )

        corpo = f"""
Olá!

O material de estudo da aula já está disponível.

INFORMAÇÕES DA AULA

Título: {titulo}
Disciplina: {disciplina}
Professor: {professor}
Data: {data}

O documento PDF está anexado a este e-mail.

O material contém o resumo da aula,
os principais conceitos apresentados,
as atividades e os trabalhos registrados
durante a explicação do professor.

Este documento foi produzido pelo Agente de
Acessibilidade Educacional.

IMPORTANTE:

O conteúdo pode conter informações processadas
por inteligência artificial. Confirme atividades,
prazos e informações importantes com o professor.

Bons estudos!

Agente de Acessibilidade Educacional
Projeto IHC - IFPR
""".strip()

        mensagem.set_content(corpo)

        with arquivo.open("rb") as f:

            mensagem.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=arquivo.name
            )

        return mensagem

    # ==========================================
    # Conexão SMTP
    # ==========================================

    def conectar(self):

        contexto = ssl.create_default_context()

        if self.porta == 465:

            servidor = smtplib.SMTP_SSL(
                self.host,
                self.porta,
                timeout=self.timeout,
                context=contexto
            )

        else:

            servidor = smtplib.SMTP(
                self.host,
                self.porta,
                timeout=self.timeout
            )

            try:

                servidor.ehlo()

                servidor.starttls(
                    context=contexto
                )

                servidor.ehlo()

            except Exception:

                servidor.close()

                raise

        try:

            servidor.login(
                self.usuario,
                self.senha
            )

        except Exception:

            servidor.close()

            raise

        return servidor

    # ==========================================
    # Envio do PDF
    # ==========================================

    def enviar(
        self,
        destinatarios,
        arquivo,
        aula
    ):

        self.validar_configuracao()

        destinatarios = (
            self.normalizar_destinatarios(
                destinatarios
            )
        )

        arquivo = self.validar_pdf(
            arquivo
        )

        enviados = []

        falhas = []

        servidor = None

        try:

            servidor = self.conectar()

            for destinatario in destinatarios:

                try:

                    mensagem = (
                        self.criar_mensagem(
                            destinatario,
                            arquivo,
                            aula
                        )
                    )

                    servidor.send_message(
                        mensagem
                    )

                    enviados.append(
                        destinatario
                    )

                    print(
                        "[Email] Envio concluído."
                    )

                except Exception as erro:

                    falhas.append({
                        "destinatario": destinatario,
                        "erro": type(erro).__name__
                    })

                    print(
                        "[Email] Falha no envio: "
                        f"{type(erro).__name__}"
                    )

        except Exception as erro:

            for destinatario in destinatarios:

                if destinatario not in enviados:

                    falhas.append({
                        "destinatario": destinatario,
                        "erro": type(erro).__name__
                    })

            print(
                "[Email] Falha de conexão SMTP: "
                f"{type(erro).__name__}"
            )

        finally:

            if servidor is not None:

                try:

                    servidor.quit()

                except Exception:

                    servidor.close()

        return {
            "sucesso": len(falhas) == 0,
            "arquivo": str(arquivo),
            "total_destinatarios": len(
                destinatarios
            ),
            "total_enviados": len(enviados),
            "total_falhas": len(falhas),
            "enviados": enviados,
            "falhas": falhas
        }