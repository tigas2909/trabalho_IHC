#iniciar aula
comandos_iniciar_aula=[
    'iniciar aula'
]

#finalizar aula
comandos_finalizar_aula=[
    'finalizar aula'
]

#iniciar tarefa
comandos_iniciar_tarefa=[
    'iniciar tarefa'
]

#finalizar tarefa
comandos_finalizar_tarefa=[
    'finalizar tarefa'
]

#iniciar trabalho
comandos_iniciar_trabalho=[
    'iniciar trabalho'
]

#finalizar trabalho
comandos_finalizar_trabalho=[
    'finalizar trabalho'
]

#iniciar destaque
comandos_iniciar_destaque=[
    'iniciar destaque'
]

#finalizar destaque
comandos_finalizar_destaque=[
    'finalizar destaque'
]

def comandos(texto):
    texto = texto.lower().strip()
    #inicio
    if texto in comandos_iniciar_aula:
        return 'iniciar_aula'
    elif texto in comandos_iniciar_tarefa:
        return 'iniciar_tarefa'
    elif texto in comandos_iniciar_trabalho:
        return 'iniciar_trabalho'
    elif texto in comandos_iniciar_destaque:
        return 'iniciar_destaque'
    
    #finalizar
    elif texto in comandos_finalizar_aula:
        return 'finalizar_aula'
    elif texto in comandos_finalizar_tarefa:
        return 'finalizar_tarefa'
    elif texto in comandos_finalizar_trabalho:
        return 'finalizar_trabalho'
    elif texto in comandos_finalizar_destaque:
        return 'finalizar_destaque'
    else:
        return None


    
