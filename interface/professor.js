"use strict";

// ==========================================
// ELEMENTOS E ESTADOS
// ==========================================

const elemento = id => document.getElementById(id);

let atualizando = false;

let configuracaoCarregada = false;

let ultimaAtualizacao = "";

let statusAtual = null;

const estados = {
    aguardando: "Aguardando início",
    conteudo: "Conteúdo",
    atividade: "Atividade",
    trabalho: "Trabalho",
    finalizado: "Finalizado"
};

// ==========================================
// FEEDBACK
// ==========================================

function feedback(texto, erro = false) {

    const campo = elemento("feedback");

    campo.textContent = texto;

    campo.classList.toggle(
        "erro",
        erro
    );

}

// ==========================================
// REQUISIÇÕES HTTP
// ==========================================

async function requisicao(url, dados = {}) {

    const resposta = await fetch(url, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(dados),

        cache: "no-store"

    });

    let resultado;

    try {

        resultado = await resposta.json();

    } catch {

        throw new Error(
            "Resposta inválida do servidor."
        );

    }

    if (!resposta.ok) {

        throw new Error(
            resultado.detail
            || "Erro na comunicação."
        );

    }

    return resultado;

}

// ==========================================
// CONFIGURAR AULA
// ==========================================

async function configurarAula() {

    try {

        await requisicao(
            "/api/professor/configurar",
            {
                titulo: elemento("titulo").value,

                professor: elemento("professor").value,

                disciplina: elemento("disciplina").value,

                vocabulario: elemento("vocabulario").value
            }
        );

        feedback(
            "Configuração salva."
        );

        return true;

    } catch (erro) {

        feedback(
            erro.message,
            true
        );

        return false;

    }

}

// ==========================================
// COMANDOS
// ==========================================

async function comando(texto) {

    try {

        if (texto === "iniciar aula") {

            const configurado = (
                await configurarAula()
            );

            if (!configurado) {
                return;
            }

        }

        if (texto === "finalizar aula") {

            const confirmou = confirm(
                "Deseja finalizar a aula "
                + "e gerar o material?"
            );

            if (!confirmou) {
                return;
            }

        }

        await requisicao(
            "/api/professor/texto",
            {
                texto
            }
        );

        feedback(
            "Comando executado: " + texto
        );

        await atualizarStatus();

    } catch (erro) {

        feedback(
            erro.message,
            true
        );

    }

}

// ==========================================
// TEXTO MANUAL
// ==========================================

async function enviarTexto() {

    const campo = elemento(
        "textoManual"
    );

    const texto = campo.value.trim();

    if (!texto) {
        return;
    }

    try {

        await requisicao(
            "/api/professor/texto",
            {
                texto
            }
        );

        campo.value = "";

        feedback(
            "Legenda enviada."
        );

        await atualizarStatus();

    } catch (erro) {

        feedback(
            erro.message,
            true
        );

    }

}

// ==========================================
// MICROFONE FÍSICO
// ==========================================

async function controlarMicrofoneLocal(acao) {

    try {

        await requisicao(
            "/api/professor/microfone/" + acao
        );

        feedback(
            acao === "iniciar"

            ? "Inicialização do microfone físico solicitada."

            : "Microfone físico desligado."
        );

        await atualizarStatus();

    } catch (erro) {

        feedback(
            erro.message,
            true
        );

    }

}

// ==========================================
// HISTÓRICO
// ==========================================

function renderizarHistorico(registros) {

    const identificador = (
        JSON.stringify(registros)
    );

    if (
        identificador
        === ultimaAtualizacao
    ) {
        return;
    }

    ultimaAtualizacao = identificador;

    const historico = elemento(
        "historico"
    );

    historico.replaceChildren();

    for (const registro of registros) {

        const div = document.createElement(
            "div"
        );

        div.className = "registro";

        if (registro.importante) {

            div.classList.add(
                "importante"
            );

        }

        const categoria = (
            document.createElement("small")
        );

        const tipo = (
            estados[registro.tipo]
            || registro.tipo
            || "Conteúdo"
        );

        categoria.textContent = (
            tipo
            + (
                registro.importante
                ? " | IMPORTANTE"
                : ""
            )
        );

        const texto = (
            document.createElement("div")
        );

        texto.textContent = (
            registro.texto || ""
        );

        div.append(
            categoria,
            texto
        );

        historico.appendChild(div);

    }

    historico.scrollTop = (
        historico.scrollHeight
    );

}

// ==========================================
// CONFIGURAR INDICADORES
// ==========================================

function atualizarIndicadores(dados) {

    const local = Boolean(
        dados.microfone_local_ativo
    );

    const remoto = Boolean(
        dados.microfone_remoto_ativo
    );

    elemento(
        "indicadorLocal"
    ).classList.toggle(
        "ativo",
        local
    );

    elemento(
        "indicadorRemoto"
    ).classList.toggle(
        "ativo",
        remoto
    );

    elemento(
        "fonteLocal"
    ).classList.toggle(
        "ativa",
        local
    );

    elemento(
        "fonteRemota"
    ).classList.toggle(
        "ativa",
        remoto
    );

    elemento(
        "statusLocal"
    ).textContent = local

        ? (
            dados.modo_microfone === "local"
            ? dados.mensagem_microfone
            : "Microfone físico ativo."
        )

        : "Microfone físico desligado.";

    const ativa = [

        "conteudo",

        "atividade",

        "trabalho"

    ].includes(
        dados.aula.estado
    );

    const remotoOcupado = (

        remoto

        || (

            typeof microfoneRemotoOcupado
            === "function"

            && microfoneRemotoOcupado()

        )

    );

    elemento(
        "iniciarLocal"
    ).disabled = (

        local

        || remotoOcupado

        || (
            ativa
            && dados.modo_microfone !== "local"
        )

    );

    elemento(
        "pararLocal"
    ).disabled = !local;

    elemento(
        "conectarRemoto"
    ).disabled = (

        local

        || remotoOcupado

        || (
            ativa
            && dados.modo_microfone !== "remoto"
        )

    );

    // O navegador que iniciou a captura
    // é responsável por desconectá-la.

    const conectadoNesteNavegador = (

        typeof microfoneRemotoOcupado
        === "function"

        && microfoneRemotoOcupado()

    );

    elemento(
        "desconectarRemoto"
    ).disabled = (
        !conectadoNesteNavegador
    );

}

// ==========================================
// TELEMETRIA
// ==========================================

function atualizarTelemetria(dados) {

    const audio = (
        dados.audio_remoto || {}
    );

    elemento("blocos").textContent = (
        audio.total_blocos || 0
    );

    elemento("bytes").textContent = (

        (
            (audio.total_bytes || 0)
            / 1024
        ).toFixed(1)

        + " KB"

    );

    elemento("fila").textContent = (
        audio.fila || 0
    );

    elemento("transcricoes").textContent = (
        audio.total_transcricoes || 0
    );

}

// ==========================================
// ATUALIZAR PAINEL
// ==========================================

async function atualizarStatus() {

    if (atualizando) {
        return;
    }

    atualizando = true;

    try {

        const resposta = await fetch(
            "/api/professor/status",
            {
                cache: "no-store"
            }
        );

        if (!resposta.ok) {

            throw new Error(
                "Servidor indisponível "
                + "ou acesso bloqueado."
            );

        }

        const dados = (
            await resposta.json()
        );

        statusAtual = dados;

        const aula = dados.aula;

        const registros = (
            dados.registros || []
        );

        const ativa = [

            "conteudo",

            "atividade",

            "trabalho"

        ].includes(
            aula.estado
        );

        // ================================
        // CONFIGURAÇÃO INICIAL
        // ================================

        if (
            !configuracaoCarregada
            && dados.configuracao
        ) {

            elemento("titulo").value = (
                dados.configuracao.titulo
            );

            elemento("professor").value = (
                dados.configuracao.professor
            );

            elemento("disciplina").value = (
                dados.configuracao.disciplina
            );

            elemento("vocabulario").value = (
                dados.vocabulario || "geral"
            );

            configuracaoCarregada = true;

            feedback(
                "Painel conectado."
            );

        }

        // ================================
        // STATUS DA AULA
        // ================================

        elemento("estado").textContent = (

            estados[aula.estado]

            || aula.estado

        );

        elemento("microfone").textContent = (

            dados.microfone

            || "Desligado"

        );

        elemento("mensagemMicrofone").textContent = (

            dados.mensagem_microfone

            || ""

        );

        elemento("modoMicrofone").textContent = (

            dados.modo_microfone === "local"

            ? "Microfone físico"

            : "Microfone do celular"

        );

        elemento("alunos").textContent = (
            dados.alunos_conectados || 0
        );

        elemento("total").textContent = (
            dados.total_registros || 0
        );

        // ================================
        // CONTROLES
        // ================================

        elemento("iniciar").disabled = (

            ativa

            || dados.processando

        );

        elemento("salvarConfiguracao").disabled = (

            ativa

            || dados.processando

        );

        document.querySelectorAll(

            "[data-durante]"

        ).forEach(botao => {

            botao.disabled = !ativa;

        });

        // ================================
        // MICROFONES
        // ================================

        atualizarIndicadores(dados);

        atualizarTelemetria(dados);

        // ================================
        // LEGENDA DEFINITIVA
        // ================================

        if (registros.length > 0) {

            elemento("legenda").textContent = (

                registros[
                    registros.length - 1
                ].texto

            );

        } else {

            elemento("legenda").textContent = (

                ativa

                ? "Pode começar a falar..."

                : "Aguardando início da aula..."

            );

        }

        // ================================
        // LEGENDA PARCIAL
        // ================================

        elemento("parcial").textContent = (

            ativa

            ? (
                dados.legenda_parcial || ""
            )

            : ""

        );

        // ================================
        // HISTÓRICO
        // ================================

        renderizarHistorico(
            registros
        );

        // ================================
        // MATERIAL DA AULA
        // ================================

        if (dados.processamento) {

            elemento(
                "processamento"
            ).textContent = (

                dados.processamento.dados.mensagem

                || dados.processamento.evento

            );

            elemento(
                "processamento"
            ).classList.toggle(

                "erro",

                dados.processamento.evento
                === "erro_processamento"

            );

        } else {

            elemento(
                "processamento"
            ).textContent = (
                "Aguardando finalização da aula."
            );

            elemento(
                "processamento"
            ).classList.remove("erro");

        }

    } catch (erro) {

        feedback(
            erro.message,
            true
        );

    } finally {

        atualizando = false;

    }

}

// ==========================================
// INICIALIZAÇÃO
// ==========================================

document.addEventListener(

    "DOMContentLoaded",

    () => {

        atualizarStatus();

        setInterval(
            atualizarStatus,
            1000
        );

    }

);