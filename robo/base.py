from .comandos.modos import comandos
from .comandos.comandos import (
    iniciar_aula,
    finalizar_aula,
    comando_enviar_resumo,
    comando_enviar_transcricao,
    comando_enviar_pdf
)

from datetime import datetime


# Arquivos utilizados nos testes
ARQUIVOS = {
    "pdf": "teste_envio_email.pdf",
    "resumo": "teste.txt",
    "transcricao": "teste.json"
}


def data_atual():
    return datetime.now().strftime("%d/%m/%Y")


def solicitar_email():
    while True:
        email = input("E-mail do destinatário: ").strip()

        if email.lower() == "cancelar":
            return None

        if "@" in email and "." in email.split("@")[-1]:
            return email

        print("[ERRO] E-mail inválido. Digite novamente ou 'cancelar'.")


def executar_envio(funcao, arquivo):
    email = solicitar_email()

    if email is None:
        print("[INFO] Envio cancelado.")
        return

    try:
        resultado = funcao(email, arquivo, data_atual())

        if resultado is False:
            print("[ERRO] A função informou falha no envio.")
        else:
            print(f"[OK] Comando executado. Retorno: {resultado}")

    except (OSError, ValueError) as erro:
        print(f"[ERRO] Falha durante o envio: {erro}")


def executar_comando(texto):
    texto = " ".join(texto.lower().strip().split())

    if not texto:
        return

    try:
        if texto == "iniciar aula":
            aula = input("Nome da aula: ").strip()
            professor = input("Nome do professor: ").strip()

            if not aula or not professor:
                print("[ERRO] Aula e professor são obrigatórios.")
                return

            resultado = iniciar_aula(
                aula,
                professor,
                data_atual()
            )

            print(f"[INICIAR AULA] Resultado: {resultado}")

        elif texto == "finalizar aula":
            resultado = finalizar_aula(
                ARQUIVOS["pdf"],
                data_atual()
            )

            print(f"[FINALIZAR AULA] Resultado: {resultado}")

        elif texto == "enviar pdf":
            executar_envio(
                comando_enviar_pdf,
                ARQUIVOS["pdf"]
            )

        elif texto == "enviar resumo":
            executar_envio(
                comando_enviar_resumo,
                ARQUIVOS["resumo"]
            )

        elif texto in ("enviar transcricao", "enviar transcrição"):
            executar_envio(
                comando_enviar_transcricao,
                ARQUIVOS["transcricao"]
            )

        else:
            resultado = comandos(texto)

            if resultado:
                print(f"[OK] {resultado}")
            else:
                print(f"[AVISO] Comando não reconhecido: {texto}")

    except Exception as erro:
        print(f"[ERRO] {type(erro).__name__}: {erro}")


def main():
    print("=" * 45)
    print("         IHC - TERMINAL DE TESTES")
    print("=" * 45)

    print("""
Comandos disponíveis:

  iniciar aula
  finalizar aula
  enviar pdf
  enviar resumo
  enviar transcricao
  sair

Digite 'cancelar' para cancelar um envio.
""")

    try:
        while True:
            texto = input("\nIHC > ").strip()

            if texto.lower() == "sair":
                print("[SISTEMA] Encerrando testes...")
                break

            executar_comando(texto)

    except (KeyboardInterrupt, EOFError):
        print("\n[SISTEMA] Programa encerrado pelo usuário.")


if __name__ == "__main__":
    main()