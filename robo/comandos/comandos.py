from ..funcoes.email import enviar_resumo_pdf, enviar_transcricao, enviar_resumo

def iniciar_aula(aula, professor, data):
    #funcoes de gerar a aula precisa do nome da aula/materia, nome do professor(a) principal e a data e horario de inicio
    
    #marcar que iniciou a aula
    return True


def finalizar_aula(nome_arquivo, data):
    #chama a funcao de enviar o resumo em pdf para todos os alunos
    enviar_resumo_pdf(nome_arquivo, data, None)
    #marca que finalizou a aula
    return False

def comando_enviar_pdf(email, arquivo, data):
    #enviando email
    resultado = enviar_resumo_pdf(arquivo, data, email)
    return resultado

def comando_enviar_resumo(email, arquivo, data):
    #enviando email
    resultado = enviar_resumo(arquivo, data, email)
    return resultado

def comando_enviar_transcricao(email, arquivo, data):
    #enviando email
    resultado = enviar_transcricao(arquivo, data, email)
    return resultado