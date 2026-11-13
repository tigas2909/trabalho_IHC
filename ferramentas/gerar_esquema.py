import json

from pathlib import Path


# ==========================================
# Tipos básicos
# ==========================================

TEXTO = {"type": "string"}

TEXTO_NULO = {
    "type": ["string", "null"]
}

INTEIRO = {
    "type": "integer",
    "minimum": 0
}

INTEIRO_NULO = {
    "type": ["integer", "null"],
    "minimum": 0
}

NUMERO_NULO = {
    "type": ["number", "null"],
    "minimum": 0
}

BOOLEANO = {
    "type": "boolean"
}

BOOLEANO_NULO = {
    "type": ["boolean", "null"]
}

ID = {
    "type": "string",
    "minLength": 1
}

DATA = {
    "type": ["string", "null"],
    "format": "date"
}

DATA_HORA = {
    "type": ["string", "null"],
    "format": "date-time"
}

HORARIO = {
    "type": ["string", "null"],
    "pattern": r"^([01]\d|2[0-3]):[0-5]\d$"
}


# ==========================================
# Funções auxiliares
# ==========================================

def lista(tipo):

    return {
        "type": "array",
        "items": tipo
    }


def objeto(campos):

    return {
        "type": "object",
        "properties": campos,
        "required": list(campos.keys()),
        "additionalProperties": False
    }


def enumeracao(*valores, permite_nulo=False):

    valores = list(valores)

    if permite_nulo:

        valores.append(None)

    return {
        "enum": valores
    }


def referencia(nome):

    return {
        "$ref": f"#/$defs/{nome}"
    }


LISTA_TEXTOS = lista(TEXTO)

REFERENCIAS = {
    "type": "array",
    "items": {
        "type": "integer",
        "minimum": 1
    },
    "uniqueItems": True
}


DIFICULDADE = enumeracao(
    "basico",
    "intermediario",
    "avancado",
    permite_nulo=True
)

MODALIDADE = enumeracao(
    "individual",
    "dupla",
    "grupo",
    permite_nulo=True
)


# ==========================================
# Definições reutilizáveis
# ==========================================

definicoes = {}


definicoes["prazo"] = objeto({

    "informado": BOOLEANO,

    "descricao_original": TEXTO_NULO,

    "data": DATA,

    "horario": HORARIO
})


definicoes["topico"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "descricao": TEXTO,

    "explicacao": TEXTO,

    "subtopicos": LISTA_TEXTOS,

    "importancia": enumeracao(
        "baixa",
        "media",
        "alta",
        permite_nulo=True
    ),

    "referencias_transcricao": REFERENCIAS
})


definicoes["conceito"] = objeto({

    "id": ID,

    "nome": TEXTO,

    "definicao": TEXTO,

    "explicacao": TEXTO,

    "exemplo": TEXTO_NULO,

    "aplicacao_pratica": TEXTO_NULO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["exemplo"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "descricao": TEXTO,

    "demonstracao": TEXTO,

    "resultado": TEXTO_NULO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["variavel"] = objeto({

    "simbolo": TEXTO,

    "significado": TEXTO,

    "unidade": TEXTO_NULO
})


definicoes["formula"] = objeto({

    "id": ID,

    "nome": TEXTO,

    "expressao": TEXTO,

    "descricao": TEXTO,

    "variaveis": lista(
        referencia("variavel")
    ),

    "exemplo_de_aplicacao": TEXTO_NULO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["codigo"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "linguagem": TEXTO_NULO,

    "codigo": TEXTO,

    "explicacao": TEXTO,

    "resultado_esperado": TEXTO_NULO,

    "completo": BOOLEANO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["etapa_procedimento"] = objeto({

    "ordem": {
        "type": "integer",
        "minimum": 1
    },

    "instrucao": TEXTO,

    "observacao": TEXTO_NULO
})


definicoes["procedimento"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "objetivo": TEXTO,

    "etapas": lista(
        referencia("etapa_procedimento")
    ),

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Atividades
# ==========================================

definicoes["atividade"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "descricao": TEXTO,

    "objetivo": TEXTO_NULO,

    "instrucoes": LISTA_TEXTOS,

    "requisitos": LISTA_TEXTOS,

    "materiais_necessarios": LISTA_TEXTOS,

    "tipo": enumeracao(
        "pratica",
        "teorica",
        "pesquisa",
        "exercicio",
        "outro",
        permite_nulo=True
    ),

    "modalidade": MODALIDADE,

    "prazo": referencia("prazo"),

    "entrega": objeto({

        "necessaria": BOOLEANO_NULO,

        "formato": TEXTO_NULO,

        "plataforma": TEXTO_NULO,

        "orientacoes": LISTA_TEXTOS
    }),

    "avaliacao": objeto({

        "avaliativa": BOOLEANO_NULO,

        "valor": NUMERO_NULO,

        "criterios": LISTA_TEXTOS
    }),

    "observacoes": LISTA_TEXTOS,

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Trabalhos
# ==========================================

definicoes["etapa_trabalho"] = objeto({

    "ordem": {
        "type": "integer",
        "minimum": 1
    },

    "titulo": TEXTO,

    "descricao": TEXTO,

    "prazo": DATA
})


definicoes["trabalho"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "descricao": TEXTO,

    "objetivo": TEXTO_NULO,

    "instrucoes": LISTA_TEXTOS,

    "requisitos_funcionais": LISTA_TEXTOS,

    "requisitos_nao_funcionais": LISTA_TEXTOS,

    "materiais_necessarios": LISTA_TEXTOS,

    "modalidade": MODALIDADE,

    "quantidade_integrantes": {
        "type": ["integer", "null"],
        "minimum": 1
    },

    "etapas": lista(
        referencia("etapa_trabalho")
    ),

    "prazo": referencia("prazo"),

    "entrega": objeto({

        "formato": TEXTO_NULO,

        "plataforma": TEXTO_NULO,

        "arquivos_necessarios": LISTA_TEXTOS,

        "orientacoes": LISTA_TEXTOS
    }),

    "avaliacao": objeto({

        "valor": NUMERO_NULO,

        "criterios": LISTA_TEXTOS,

        "apresentacao_obrigatoria": (
            BOOLEANO_NULO
        )
    }),

    "observacoes": LISTA_TEXTOS,

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Avaliações
# ==========================================

definicoes["avaliacao"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "tipo": enumeracao(
        "prova",
        "seminario",
        "trabalho",
        "atividade",
        "projeto",
        "outro",
        permite_nulo=True
    ),

    "descricao": TEXTO,

    "conteudos_cobrados": LISTA_TEXTOS,

    "data": DATA,

    "horario": HORARIO,

    "valor": NUMERO_NULO,

    "criterios": LISTA_TEXTOS,

    "orientacoes": LISTA_TEXTOS,

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Prazos
# ==========================================

definicoes["prazo_geral"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "tipo": enumeracao(
        "atividade",
        "trabalho",
        "avaliacao",
        "outro"
    ),

    "referencia_id": TEXTO_NULO,

    "descricao_original": TEXTO,

    "data": DATA,

    "horario": HORARIO,

    "confirmado": BOOLEANO,

    "observacoes": LISTA_TEXTOS
})


# ==========================================
# Materiais complementares
# ==========================================

definicoes["material"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "tipo": enumeracao(
        "livro",
        "artigo",
        "video",
        "site",
        "documento",
        "codigo",
        "outro"
    ),

    "descricao": TEXTO,

    "url": TEXTO_NULO,

    "obrigatorio": BOOLEANO_NULO,

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Revisão
# ==========================================

definicoes["pergunta"] = objeto({

    "id": ID,

    "pergunta": TEXTO,

    "resposta": TEXTO,

    "explicacao": TEXTO,

    "dificuldade": DIFICULDADE,

    "referencias_transcricao": REFERENCIAS
})


definicoes["exercicio"] = objeto({

    "id": ID,

    "titulo": TEXTO,

    "enunciado": TEXTO,

    "tipo": enumeracao(
        "objetiva",
        "discursiva",
        "verdadeiro_falso",
        "pratica"
    ),

    "alternativas": LISTA_TEXTOS,

    "resposta": TEXTO_NULO,

    "explicacao": TEXTO_NULO,

    "gerado_pela_ia": {
        "const": True
    },

    "referencias_transcricao": REFERENCIAS
})


definicoes["flashcard"] = objeto({

    "id": ID,

    "frente": TEXTO,

    "verso": TEXTO,

    "categoria": TEXTO
})


# ==========================================
# Acessibilidade
# ==========================================

definicoes["termo_tecnico"] = objeto({

    "termo": TEXTO,

    "significado": TEXTO_NULO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["referencia_visual"] = objeto({

    "descricao": TEXTO,

    "tipo": enumeracao(
        "imagem",
        "slide",
        "quadro",
        "video",
        "demonstracao",
        "outro"
    ),

    "conteudo_disponivel": BOOLEANO,

    "informacao_ausente": TEXTO_NULO,

    "referencias_transcricao": REFERENCIAS
})


definicoes["trecho_incompleto"] = objeto({

    "texto": TEXTO,

    "motivo": TEXTO,

    "necessita_confirmacao": BOOLEANO,

    "referencias_transcricao": REFERENCIAS
})


# ==========================================
# Estrutura principal
# ==========================================

esquema = objeto({

    "versao_esquema": {
        "const": "1.0"
    },

    "identificacao": objeto({

        "aula_id": ID,

        "titulo": TEXTO,

        "disciplina": TEXTO_NULO,

        "professor": TEXTO_NULO,

        "data": DATA,

        "inicio": DATA_HORA,

        "fim": DATA_HORA,

        "duracao_segundos": INTEIRO,

        "idioma": {
            "const": "pt-BR"
        }
    }),

    "resumo": objeto({

        "resumo_geral": TEXTO,

        "objetivos_da_aula": LISTA_TEXTOS,

        "assuntos_principais": LISTA_TEXTOS,

        "palavras_chave": LISTA_TEXTOS,

        "nivel_de_dificuldade": DIFICULDADE
    }),

    "conteudo": objeto({

        "topicos": lista(
            referencia("topico")
        ),

        "conceitos": lista(
            referencia("conceito")
        ),

        "exemplos": lista(
            referencia("exemplo")
        ),

        "formulas": lista(
            referencia("formula")
        ),

        "codigos": lista(
            referencia("codigo")
        ),

        "procedimentos": lista(
            referencia("procedimento")
        )
    }),

    "atividades": lista(
        referencia("atividade")
    ),

    "trabalhos": lista(
        referencia("trabalho")
    ),

    "avaliacoes": lista(
        referencia("avaliacao")
    ),

    "prazos": lista(
        referencia("prazo_geral")
    ),

    "materiais_complementares": lista(
        referencia("material")
    ),

    "revisao": objeto({

        "pontos_principais": LISTA_TEXTOS,

        "conceitos_fundamentais": LISTA_TEXTOS,

        "perguntas_e_respostas": lista(
            referencia("pergunta")
        ),

        "exercicios_de_fixacao": lista(
            referencia("exercicio")
        ),

        "flashcards": lista(
            referencia("flashcard")
        ),

        "sugestao_de_estudo": LISTA_TEXTOS
    }),

    "acessibilidade": objeto({

        "termos_tecnicos": lista(
            referencia("termo_tecnico")
        ),

        "referencias_visuais": lista(
            referencia("referencia_visual")
        ),

        "trechos_incompletos": lista(
            referencia("trecho_incompleto")
        ),

        "adaptacoes_textuais": LISTA_TEXTOS,

        "informacoes_que_precisam_de_confirmacao": (
            LISTA_TEXTOS
        )
    }),

    "observacoes": objeto({

        "avisos_do_professor": LISTA_TEXTOS,

        "informacoes_adicionais": LISTA_TEXTOS,

        "contradicoes_identificadas": LISTA_TEXTOS,

        "limitacoes_da_transcricao": LISTA_TEXTOS,

        "informacoes_nao_confirmadas": LISTA_TEXTOS
    }),

    "qualidade_do_processamento": objeto({

        "conteudo_suficiente": BOOLEANO_NULO,

        "total_registros_analisados": (
            INTEIRO_NULO
        ),

        "total_registros_utilizados": (
            INTEIRO_NULO
        ),

        "registros_incompletos": REFERENCIAS,

        "campos_sem_informacao": LISTA_TEXTOS,

        "necessita_revisao_humana": BOOLEANO_NULO,

        "motivos_para_revisao": LISTA_TEXTOS
    })
})


esquema["$schema"] = (
    "https://json-schema.org/draft/2020-12/schema"
)

esquema["title"] = (
    "Resumo de Aula - Agente IHC"
)

esquema["description"] = (
    "Esquema de validação dos materiais de "
    "estudo gerados pela inteligência artificial."
)

esquema["$defs"] = definicoes


# ==========================================
# Salvar arquivo
# ==========================================

def gerar_esquema():

    diretorio = (
        Path(__file__).resolve().parent.parent
        / "robo"
    )

    diretorio.mkdir(
        parents=True,
        exist_ok=True
    )

    arquivo = (
        diretorio
        / "esquema_resumo.json"
    )

    with arquivo.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            esquema,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"[Schema] Arquivo gerado: {arquivo}"
    )

    return arquivo


if __name__ == "__main__":

    gerar_esquema()