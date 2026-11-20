import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

caminho_resumo_pdf = Path(__file__).resolve().parent.parent.parent / 'arquivo' / 'resumo_pdf'
caminho_resumo = Path(__file__).resolve().parent.parent.parent / 'arquivo' / 'resumo'
caminho_transcricoes = Path(__file__).resolve().parent.parent.parent / 'arquivo' / 'transcricoes'


def enviar_email(destinatario, arquivo, tipo_arquivo, assunto):
    try:
        remetente = os.getenv("REMETENTE")
        senha = os.getenv("SENHA")

        mensagem = EmailMessage()

        mensagem["From"] = remetente
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto

        mensagem.set_content("Segue o arquivo em anexo.")

        caminho = Path(arquivo)

        with open(caminho, "rb") as documento:
            mensagem.add_attachment(
                documento.read(),
                maintype="application",
                subtype=tipo_arquivo,
                filename=caminho.name
            )

        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(mensagem)

        return True

    except FileNotFoundError:
        print(f"Arquivo não encontrado: {arquivo}")
        return False

    except smtplib.SMTPAuthenticationError:
        print("Erro de autenticação no e-mail.")
        return False

    except smtplib.SMTPException as erro:
        print(f"Erro SMTP: {erro}")
        return False

    except Exception as erro:
        print(f"Erro inesperado: {erro}")
        return False

def chamar_funcao(Email, nome_arquivo, tipo_envio, resumo):
    if Email is None:
        with open("emails.txt", "r", encoding="utf-8") as arquivo:
            for email in arquivo:
                email = email.strip()

                if email:
                    resposta = enviar_email(email, nome_arquivo, tipo_envio, resumo)
                    return resposta
    else:
        resposta = enviar_email(Email, nome_arquivo, tipo_envio, resumo)
        return resposta

def enviar_resumo_pdf(nome_arquivo, data, email=None):
    arquivo = caminho_resumo_pdf / nome_arquivo

    if arquivo.is_file():
        resposta = chamar_funcao(email, arquivo, "pdf", f"Resumo da aula {data}")
        return resposta
    else:
        return None


def enviar_resumo(nome_arquivo, data, email):
    arquivo = caminho_resumo / nome_arquivo

    if arquivo.is_file():
        resposta = chamar_funcao(email, arquivo, "octet-stream", f"Resumo da aula {data}")
        return resposta
    else:
        return None


def enviar_transcricao(nome_arquivo, data, email):
    arquivo = caminho_transcricoes / nome_arquivo

    if arquivo.is_file():
        resposta = chamar_funcao(email, arquivo, "json", f"Transcrição da aula {data}")
        return resposta
    else:
        return None