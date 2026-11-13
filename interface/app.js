"use strict";

// ==========================================
// CONFIGURAÇÕES
// ==========================================

const CONFIG = {
    websocketPath: "/ws",
    reconnectDelay: 3000,
    maxHistory: 500,
    minFontSize: 18,
    maxFontSize: 72,
    fontStep: 2,
    defaultFontSize: 28
};


// ==========================================
// ESTADO DA INTERFACE
// ==========================================

const state = {
    socket: null,
    reconnectTimer: null,
    connected: false,

    lessonId: null,
    lessonStart: null,
    lessonEnd: null,
    lessonState: "aguardando",

    history: [],
    filter: "todos",

    fontSize: CONFIG.defaultFontSize,
    highContrast: false,
    autoScroll: true,

    receivedIds: new Set(),
    nextLocalId: 1,

    partialCaption: "",
    lastCaption: null,

    microphoneMode: null,
    microphoneState: "parado",

    processing: null
};


// ==========================================
// ELEMENTOS HTML
// ==========================================

const elements = {

    connectionStatus:
        document.getElementById("connection-status"),

    connectionText:
        document.getElementById("connection-text"),

    lessonTitle:
        document.getElementById("lesson-title"),

    lessonSubtitle:
        document.getElementById("lesson-subtitle"),

    lessonStatus:
        document.getElementById("lesson-status"),

    professor:
        document.getElementById("professor"),

    discipline:
        document.getElementById("discipline"),

    timer:
        document.getElementById("lesson-timer"),

    currentCaption:
        document.getElementById("current-caption"),

    captionTime:
        document.getElementById("caption-time"),

    captionType:
        document.getElementById("caption-type"),

    liveText:
        document.getElementById("live-text"),

    history:
        document.getElementById("history"),

    fontSize:
        document.getElementById("font-size"),

    fontDecrease:
        document.getElementById("font-decrease"),

    fontIncrease:
        document.getElementById("font-increase"),

    contrastToggle:
        document.getElementById("contrast-toggle"),

    fullscreenToggle:
        document.getElementById("fullscreen-toggle"),

    pauseToggle:
        document.getElementById("pause-toggle"),

    clearHistory:
        document.getElementById("clear-history"),

    importantPanel:
        document.getElementById("important-panel"),

    importantContent:
        document.getElementById("important-content"),

    processingPanel:
        document.getElementById("processing-panel"),

    processingTitle:
        document.getElementById("processing-title"),

    processingMessage:
        document.getElementById("processing-message"),

    processingIcon:
        document.getElementById("processing-icon")
};


// ==========================================
// FUNÇÕES AUXILIARES
// ==========================================

function isLessonActive() {

    return [
        "conteudo",
        "atividade",
        "trabalho"
    ].includes(
        state.lessonState
    );

}


function belongsToCurrentLesson(data) {

    if (
        data.aula_id &&
        state.lessonId &&
        data.aula_id !== state.lessonId
    ) {

        return false;

    }

    return true;

}


function resetCaptionStyle() {

    elements.currentCaption.style.fontStyle =
        "normal";

    elements.currentCaption.style.opacity =
        "1";

}


function normalizeText(value) {

    return typeof value === "string"
        ? value.trim()
        : "";

}


// ==========================================
// CONFIGURAÇÕES DE ACESSIBILIDADE
// ==========================================

function savePreferences() {

    try {

        localStorage.setItem(

            "agente-ihc-preferences",

            JSON.stringify({

                fontSize: state.fontSize,

                highContrast: state.highContrast,

                autoScroll: state.autoScroll

            })

        );

    } catch (error) {

        console.warn(
            "Não foi possível salvar as preferências.",
            error
        );

    }

}


function loadPreferences() {

    try {

        const raw = localStorage.getItem(
            "agente-ihc-preferences"
        );

        if (!raw) {

            return;

        }

        const preferences = JSON.parse(raw);

        if (Number.isFinite(preferences.fontSize)) {

            state.fontSize = Math.max(

                CONFIG.minFontSize,

                Math.min(

                    CONFIG.maxFontSize,

                    preferences.fontSize

                )

            );

        }

        state.highContrast =
            preferences.highContrast === true;

        state.autoScroll =
            preferences.autoScroll !== false;

    } catch (error) {

        console.warn(
            "Não foi possível carregar as preferências.",
            error
        );

    }

}


function applyPreferences() {

    document.documentElement.style.setProperty(

        "--caption-size",

        `${state.fontSize}px`

    );

    elements.fontSize.textContent =
        `${state.fontSize}px`;

    document.body.classList.toggle(

        "high-contrast",

        state.highContrast

    );

    elements.contrastToggle.setAttribute(

        "aria-pressed",

        String(state.highContrast)

    );

    elements.pauseToggle.setAttribute(

        "aria-pressed",

        String(!state.autoScroll)

    );

    elements.pauseToggle.textContent =

        state.autoScroll

            ? "Pausar rolagem"

            : "Retomar rolagem";

    elements.fontDecrease.disabled =
        state.fontSize <= CONFIG.minFontSize;

    elements.fontIncrease.disabled =
        state.fontSize >= CONFIG.maxFontSize;

}


function changeFontSize(amount) {

    state.fontSize = Math.max(

        CONFIG.minFontSize,

        Math.min(

            CONFIG.maxFontSize,

            state.fontSize + amount

        )

    );

    applyPreferences();

    savePreferences();

}


function toggleContrast() {

    state.highContrast =
        !state.highContrast;

    applyPreferences();

    savePreferences();

}


function toggleAutoScroll() {

    state.autoScroll =
        !state.autoScroll;

    applyPreferences();

    savePreferences();

    if (state.autoScroll) {

        scrollHistory();

    }

}


// ==========================================
// TELA CHEIA
// ==========================================

async function toggleFullscreen() {

    try {

        if (document.fullscreenElement) {

            await document.exitFullscreen();

        } else if (

            document.documentElement.requestFullscreen

        ) {

            await document.documentElement
                .requestFullscreen();

        } else {

            console.warn(
                "Tela cheia não suportada."
            );

        }

    } catch (error) {

        console.warn(
            "Não foi possível alterar a tela cheia.",
            error
        );

    }

}


document.addEventListener(

    "fullscreenchange",

    () => {

        const fullscreen = Boolean(
            document.fullscreenElement
        );

        elements.fullscreenToggle.textContent =

            fullscreen

                ? "Sair da tela cheia"

                : "Tela cheia";

        elements.fullscreenToggle.setAttribute(

            "aria-pressed",

            String(fullscreen)

        );

    }

);


// ==========================================
// STATUS DA CONEXÃO
// ==========================================

function updateConnection(status) {

    elements.connectionStatus.className =
        `connection-status ${status}`;

    const labels = {

        connected: "Conectado",

        connecting: "Conectando...",

        disconnected: "Desconectado"

    };

    elements.connectionText.textContent =
        labels[status] || "Desconectado";

    state.connected =
        status === "connected";

    if (!state.connected) {

        clearPartialCaption();

        setLiveStatus(

            false,

            status === "connecting"

                ? "Conectando ao agente..."

                : "Sem conexão com o agente"

        );

    }

}


// ==========================================
// WEBSOCKET
// ==========================================

function connectWebSocket() {

    // Evita abrir duas conexões simultâneas.

    if (

        state.socket &&

        (

            state.socket.readyState === WebSocket.OPEN

            ||

            state.socket.readyState === WebSocket.CONNECTING

        )

    ) {

        return;

    }

    // Cancela uma reconexão agendada.

    if (state.reconnectTimer !== null) {

        clearTimeout(
            state.reconnectTimer
        );

        state.reconnectTimer = null;

    }

    updateConnection("connecting");

    // HTTP utiliza ws.
    // HTTPS utiliza wss.

    const protocol =

        window.location.protocol === "https:"

            ? "wss:"

            : "ws:";

    const address =

        `${protocol}//${window.location.host}`

        + CONFIG.websocketPath;

    console.log(

        "[WebSocket] Conectando:",

        address

    );

    let socket;

    try {

        socket = new WebSocket(address);

    } catch (error) {

        console.error(

            "[WebSocket] Falha ao criar conexão:",

            error

        );

        updateConnection("disconnected");

        scheduleReconnect();

        return;

    }

    state.socket = socket;


    // ======================================
    // CONEXÃO ABERTA
    // ======================================

    socket.onopen = () => {

        if (state.socket !== socket) {

            return;

        }

        console.log(
            "[WebSocket] Conectado."
        );

        updateConnection("connected");

        setLiveStatus(

            false,

            isLessonActive()

                ? "Aguardando áudio"

                : "Aguardando início da aula"

        );

    };


    // ======================================
    // RECEBER MENSAGEM
    // ======================================

    socket.onmessage = event => {

        if (state.socket !== socket) {

            return;

        }

        try {

            const message = JSON.parse(
                event.data
            );

            handleMessage(message);

        } catch (error) {

            console.error(

                "[WebSocket] Mensagem inválida:",

                error

            );

        }

    };


    // ======================================
    // CONEXÃO ENCERRADA
    // ======================================

    socket.onclose = () => {

        if (state.socket !== socket) {

            return;

        }

        console.log(
            "[WebSocket] Conexão encerrada."
        );

        state.socket = null;

        updateConnection("disconnected");

        scheduleReconnect();

    };


    // ======================================
    // ERRO DE CONEXÃO
    // ======================================

    socket.onerror = () => {

        console.warn(
            "[WebSocket] Erro de conexão."
        );

        try {

            socket.close();

        } catch (error) {

            console.warn(error);

        }

    };

}


// ==========================================
// RECONECTAR WEBSOCKET
// ==========================================

function scheduleReconnect() {

    if (state.reconnectTimer !== null) {

        return;

    }

    state.reconnectTimer = setTimeout(

        () => {

            state.reconnectTimer = null;

            connectWebSocket();

        },

        CONFIG.reconnectDelay

    );

}


// ==========================================
// RECEBER EVENTOS DO AGENTE
// ==========================================

function handleMessage(message) {

    if (

        !message

        ||

        typeof message !== "object"

    ) {

        return;

    }

    const event =
        message.evento || message.event;

    const data =
        message.dados || message.data || {};

    switch (event) {


        // ==================================
        // STATUS GERAL
        // ==================================

        case "status":

            handleStatus(data);

            break;


        // ==================================
        // AULA INICIADA
        // ==================================

        case "aula_iniciada":

            startLesson(data);

            break;


        // ==================================
        // LEGENDA DEFINITIVA - WHISPER
        // ==================================

        case "legenda":

            receiveCaption(data);

            break;


        // ==================================
        // LEGENDA PARCIAL - VOSK
        // ==================================

        case "legenda_parcial":

            receivePartialCaption(data);

            break;


        // ==================================
        // ALTERAÇÃO DE ESTADO
        // ==================================

        case "estado_alterado":

            updateLessonState(
                data.estado
            );

            break;


        // ==================================
        // INFORMAÇÃO IMPORTANTE
        // ==================================

        case "informacao_importante":

            if (belongsToCurrentLesson(data)) {

                addImportant(
                    data.texto
                );

            }

            break;


        // ==================================
        // AULA FINALIZADA
        // ==================================

        case "aula_finalizada":

            finishLesson(data);

            break;


        // ==================================
        // MICROFONE
        // ==================================

        case "microfone_status":

            handleMicrophoneStatus(data);

            break;


        case "microfone_modo":

            state.microphoneMode =
                data.modo || null;

            console.log(

                "[ÁUDIO] Fonte selecionada:",

                state.microphoneMode

            );

            break;


        // ==================================
        // COMANDOS
        // ==================================

        case "comando_executado":

            console.log(

                "[COMANDO] Executado:",

                data.comando,

                data.mensagem || ""

            );

            break;


        case "comando_rejeitado":

            console.warn(

                "[COMANDO] Rejeitado:",

                data.mensagem

            );

            break;


        // ==================================
        // TRANSCRIÇÃO SALVA
        // ==================================

        case "transcricao_salva":

            showProcessing(

                "Transcrição salva",

                data.mensagem ||

                "A transcrição da aula foi salva."

            );

            break;


        // ==================================
        // GEMINI
        // ==================================

        case "resumo_pendente":

            showProcessing(

                "Preparando resumo",

                data.mensagem ||

                (

                    "A aula foi finalizada. "

                    + "O agente está organizando "

                    + "o conteúdo."

                )

            );

            break;


        case "resumo_gerado":

            showProcessing(

                "Resumo gerado",

                data.mensagem ||

                (

                    "O conteúdo da aula foi organizado "

                    + "e está sendo preparado para o PDF."

                )

            );

            break;


        // ==================================
        // PDF
        // ==================================

        case "pdf_gerado":

            showProcessing(

                "Material disponível",

                "O documento PDF foi gerado. "

                + "Aguardando conclusão do processamento."

            );

            break;


        // ==================================
        // ENVIO DE E-MAIL
        // ==================================

        case "email_enviado":

            showCompleted(

                "Material enviado",

                data.mensagem ||

                (

                    "O relatório da aula foi enviado "

                    + "aos destinatários configurados."

                )

            );

            break;


        // ==================================
        // PROCESSAMENTO SEM E-MAIL
        // ==================================

        case "processamento_concluido":

            showCompleted(

                "Material disponível",

                data.mensagem ||

                "O material da aula foi gerado."

            );

            break;


        // ==================================
        // ERRO NO PROCESSAMENTO
        // ==================================

        case "erro_processamento":

            showError(

                data.mensagem ||

                "Ocorreu uma falha no processamento."

            );

            break;


        case "erro_armazenamento":

            showError(

                data.mensagem ||

                "Não foi possível salvar a aula."

            );

            break;


        // ==================================
        // EVENTO DESCONHECIDO
        // ==================================

        default:

            console.log(

                "[WebSocket] Evento não tratado:",

                event

            );

    }

}


// ==========================================
// STATUS INICIAL / RECONEXÃO
// ==========================================

function handleStatus(data) {

    const lesson = data.aula || data;

    // ======================================
    // IDENTIFICAR AULA
    // ======================================

    if (lesson.id) {

        if (state.lessonId !== lesson.id) {

            startLesson(lesson);

        } else {

            updateLessonMetadata(lesson);

        }

        updateLessonState(

            lesson.estado || "aguardando"

        );

        if (lesson.inicio) {

            state.lessonStart =
                lesson.inicio;

        }

        if (lesson.fim) {

            state.lessonEnd =
                lesson.fim;

        }

        if (lesson.estado === "finalizado") {

            elements.lessonSubtitle.textContent =
                "A aula foi encerrada.";

        }

    } else if (

        lesson.estado === "aguardando"

    ) {

        if (state.lessonId !== null) {

            resetLesson();

        }

        updateLessonState("aguardando");

    }


    // ======================================
    // RECUPERAR HISTÓRICO
    // ======================================

    if (Array.isArray(data.registros)) {

        for (const record of data.registros) {

            receiveCaption(

                record,

                {

                    render: false,

                    announce: false

                }

            );

        }

        renderHistory();

    }


    // ======================================
    // RECUPERAR MICROFONE
    // ======================================

    if (data.modo_microfone) {

        state.microphoneMode =
            data.modo_microfone;

    }

    if (data.microfone) {

        handleMicrophoneStatus({

            estado: data.microfone,

            mensagem: data.mensagem_microfone,

            modo: data.modo_microfone

        });

    }


    // ======================================
    // RECUPERAR LEGENDA PARCIAL
    // ======================================

    if (

        typeof data.legenda_parcial === "string"

        &&

        isLessonActive()

    ) {

        receivePartialCaption({

            texto: data.legenda_parcial,

            aula_id: lesson.id

        });

    }


    // ======================================
    // RECUPERAR PROCESSAMENTO
    // ======================================

    if (

        data.processamento

        &&

        typeof data.processamento === "object"

        &&

        data.processamento.evento

    ) {

        handleMessage(
            data.processamento
        );

    } else if (

        data.processando

        &&

        state.lessonState === "finalizado"

    ) {

        showProcessing(

            "Processando aula",

            "O agente está preparando o material."

        );

    }

    updateTimer();

}


// ==========================================
// METADADOS DA AULA
// ==========================================

function updateLessonMetadata(data) {

    elements.lessonTitle.textContent =

        data.titulo ||

        "Aula em andamento";

    elements.professor.textContent =

        data.professor ||

        "Não informado";

    elements.discipline.textContent =

        data.disciplina ||

        "Não informada";

}


// ==========================================
// INICIAR AULA
// ==========================================

function startLesson(data) {

    const id = data.id || data.aula_id || null;

    // Evita apagar o histórico caso o servidor
    // envie novamente a mesma aula.

    if (

        id !== null

        &&

        id === state.lessonId

    ) {

        updateLessonMetadata(data);

        return;

    }

    state.lessonId = id;

    state.lessonStart =
        data.inicio || null;

    state.lessonEnd =
        data.fim || null;

    state.history = [];

    state.receivedIds.clear();

    state.nextLocalId = 1;

    state.partialCaption = "";

    state.lastCaption = null;

    state.processing = null;

    updateLessonMetadata(data);

    elements.lessonSubtitle.textContent =

        data.estado === "finalizado"

            ? "A aula foi encerrada."

            : "Acompanhe as legendas em tempo real.";

    elements.currentCaption.textContent =

        "Aguardando a fala do professor...";

    elements.currentCaption.className =
        "current-caption";

    resetCaptionStyle();

    elements.captionTime.textContent =
        "Aguardando transcrição";

    elements.importantPanel.hidden = true;

    elements.importantContent.replaceChildren();

    elements.processingPanel.hidden = true;

    updateLessonState(

        data.estado || "conteudo"

    );

    renderHistory();

    updateTimer();

}


// ==========================================
// LIMPAR ESTADO DA AULA
// ==========================================

function resetLesson() {

    state.lessonId = null;

    state.lessonStart = null;

    state.lessonEnd = null;

    state.lessonState = "aguardando";

    state.history = [];

    state.receivedIds.clear();

    state.nextLocalId = 1;

    state.partialCaption = "";

    state.lastCaption = null;

    state.processing = null;

    elements.lessonTitle.textContent =
        "Aguardando aula";

    elements.lessonSubtitle.textContent =
        "Aguarde o professor iniciar a aula.";

    elements.professor.textContent =
        "Não informado";

    elements.discipline.textContent =
        "Não informada";

    elements.currentCaption.textContent =
        "Aguardando início da aula...";

    elements.currentCaption.className =
        "current-caption";

    resetCaptionStyle();

    elements.captionTime.textContent =
        "Aguardando transcrição";

    elements.importantPanel.hidden = true;

    elements.importantContent.replaceChildren();

    elements.processingPanel.hidden = true;

    updateLessonState("aguardando");

    renderHistory();

    updateTimer();

}


// ==========================================
// ESTADO DA AULA
// ==========================================

function updateLessonState(value) {

    const states = {

        aguardando: {

            label: "Aguardando",

            className: "waiting"

        },

        conteudo: {

            label: "Conteúdo",

            className: "content"

        },

        atividade: {

            label: "Atividade",

            className: "activity"

        },

        trabalho: {

            label: "Trabalho",

            className: "work"

        },

        finalizado: {

            label: "Finalizada",

            className: "finished"

        }

    };

    const selected = states[value];

    if (!selected) {

        return;

    }

    state.lessonState = value;

    elements.lessonStatus.textContent =
        selected.label;

    elements.lessonStatus.className =

        `lesson-status ${selected.className}`;

    elements.captionType.textContent =
        selected.label;


    // ======================================
    // AULA FINALIZADA
    // ======================================

    if (value === "finalizado") {

        clearPartialCaption();

        setLiveStatus(

            false,

            "Aula finalizada"

        );

    }


    // ======================================
    // AGUARDANDO INÍCIO
    // ======================================

    else if (value === "aguardando") {

        clearPartialCaption();

        setLiveStatus(

            false,

            "Aguardando início da aula"

        );

    }


    // ======================================
    // AULA ATIVA
    // ======================================

    else {

        if (state.partialCaption) {

            setLiveStatus(

                true,

                "Reconhecendo áudio"

            );

        } else if (state.lastCaption) {

            setLiveStatus(

                true,

                "Recebendo legendas"

            );

        } else {

            setLiveStatus(

                false,

                "Aguardando áudio"

            );

        }

    }

}


// ==========================================
// STATUS DO MICROFONE
// ==========================================

function handleMicrophoneStatus(data) {

    if (data.modo) {

        state.microphoneMode =
            data.modo;

    }

    if (data.estado) {

        state.microphoneState =
            data.estado;

    }

    console.log(

        "[MICROFONE]",

        state.microphoneMode,

        state.microphoneState,

        data.mensagem || ""

    );

    if (!state.connected) {

        return;

    }

    if (state.lessonState === "finalizado") {

        return;

    }

    if (state.lessonState === "aguardando") {

        setLiveStatus(

            false,

            "Aguardando início da aula"

        );

        return;

    }

    const status = state.microphoneState;


    // ======================================
    // MICROFONE CARREGANDO
    // ======================================

    if (status === "carregando") {

        setLiveStatus(

            false,

            "Preparando reconhecimento de voz"

        );

        return;

    }


    // ======================================
    // MICROFONE PARADO
    // ======================================

    if (

        status === "parado"

        ||

        status === "desligado"

    ) {

        clearPartialCaption();

        setLiveStatus(

            false,

            "Microfone do professor desligado"

        );

        return;

    }


    // ======================================
    // ERRO NO MICROFONE
    // ======================================

    if (status === "erro") {

        clearPartialCaption();

        setLiveStatus(

            false,

            "Microfone indisponível"

        );

        return;

    }


    // ======================================
    // MICROFONE ESCUTANDO
    // ======================================

    if (

        status === "escutando"

        ||

        status === "ativo"

        ||

        status === "pronto"

    ) {

        setLiveStatus(

            Boolean(state.partialCaption),

            state.partialCaption

                ? "Reconhecendo áudio"

                : "Aguardando fala do professor"

        );

        return;

    }

}


// ==========================================
// LEGENDA PARCIAL - VOSK
// ==========================================

function receivePartialCaption(data) {

    if (!state.connected) {

        return;

    }

    if (!isLessonActive()) {

        return;

    }

    if (!belongsToCurrentLesson(data)) {

        return;

    }

    const texto = normalizeText(
        data.texto
    );

    // ======================================
    // LIMPAR RESULTADO PARCIAL
    // ======================================

    if (!texto) {

        clearPartialCaption();

        return;

    }

    // Não renderizar o mesmo resultado
    // parcial várias vezes.

    if (

        state.partialCaption === texto

    ) {

        return;

    }

    state.partialCaption = texto;

    // ======================================
    // EXIBIR TEXTO PROVISÓRIO
    // ======================================

    elements.currentCaption.textContent =
        texto;

    elements.currentCaption.className =

        `current-caption ${getTypeClass({

            tipo: state.lessonState,

            importante: false

        })}`;

    elements.currentCaption.style.fontStyle =
        "italic";

    elements.currentCaption.style.opacity =
        "0.75";

    elements.captionTime.textContent =
        "Transcrevendo...";

    elements.captionType.textContent =

        getTypeLabel({

            tipo: state.lessonState,

            importante: false

        });

    setLiveStatus(

        true,

        "Reconhecendo áudio"

    );

    // A legenda parcial não entra no histórico.
    // Somente o resultado definitivo será salvo.

}


// ==========================================
// LIMPAR LEGENDA PARCIAL
// ==========================================

function clearPartialCaption() {

    const tinhaParcial = Boolean(
        state.partialCaption
    );

    state.partialCaption = "";

    resetCaptionStyle();

    // Se não havia legenda parcial,
    // mantém a legenda atual.

    if (!tinhaParcial) {

        return;

    }

    // ======================================
    // RESTAURAR ÚLTIMA LEGENDA DEFINITIVA
    // ======================================

    if (state.lastCaption) {

        renderCurrentCaption(
            state.lastCaption
        );

    } else {

        elements.currentCaption.textContent =

            state.lessonState === "finalizado"

                ? "A aula foi encerrada."

                : "Aguardando a fala do professor...";

        elements.currentCaption.className =
            "current-caption";

        elements.captionTime.textContent =
            "Aguardando transcrição";

    }

    if (!state.connected) {

        setLiveStatus(

            false,

            "Sem conexão com o agente"

        );

    } else if (

        state.lessonState === "finalizado"

    ) {

        setLiveStatus(

            false,

            "Aula finalizada"

        );

    } else if (isLessonActive()) {

        setLiveStatus(

            false,

            "Aguardando áudio"

        );

    }

}


// ==========================================
// RENDERIZAR LEGENDA DEFINITIVA
// ==========================================

function renderCurrentCaption(caption) {

    if (!caption) {

        return;

    }

    elements.currentCaption.textContent =
        caption.texto;

    elements.currentCaption.className =

        `current-caption ${getTypeClass(caption)}`;

    resetCaptionStyle();

    elements.captionTime.textContent =

        `Recebida às ${formatTime(caption.horario)}`;

    elements.captionType.textContent =

        getTypeLabel(caption);

}


// ==========================================
// RECEBER LEGENDA DEFINITIVA - WHISPER
// ==========================================

function receiveCaption(

    data,

    options = {}

) {

    const render =
        options.render !== false;

    const announce =
        options.announce !== false;

    const texto = normalizeText(
        data.texto
    );

    if (!texto) {

        return;

    }

    // Evita misturar registros
    // de aulas diferentes.

    if (!belongsToCurrentLesson(data)) {

        return;

    }

    // ======================================
    // EVITAR REGISTROS DUPLICADOS
    // ======================================

    const serverId = data.id ?? null;

    if (

        serverId !== null

        &&

        state.receivedIds.has(serverId)

    ) {

        return;

    }

    if (serverId !== null) {

        state.receivedIds.add(
            serverId
        );

    }

    // ======================================
    // TIPO DE REGISTRO
    // ======================================

    const type =

        data.tipo ||

        state.lessonState ||

        "conteudo";

    // ======================================
    // CONSTRUIR LEGENDA
    // ======================================

    const caption = {

        id:

            serverId

            ??

            `local-${state.nextLocalId++}`,

        texto,

        tipo: type,

        importante:

            data.importante === true,

        horario:

            data.horario

            ||

            new Date().toISOString()

    };

    // ======================================
    // ADICIONAR AO HISTÓRICO
    // ======================================

    state.history.push(
        caption
    );

    if (

        state.history.length

        >

        CONFIG.maxHistory

    ) {

        state.history.shift();

    }

    // Armazena a última legenda definitiva
    // separadamente das parciais do Vosk.

    state.lastCaption = caption;

    state.partialCaption = "";

    renderCurrentCaption(
        caption
    );

    // ======================================
    // INFORMAÇÃO IMPORTANTE
    // ======================================

    if (caption.importante) {

        addImportant(
            caption.texto
        );

    }

    // ======================================
    // STATUS DA TRANSMISSÃO
    // ======================================

    if (

        announce

        &&

        isLessonActive()

        &&

        state.connected

    ) {

        setLiveStatus(

            true,

            "Recebendo legendas"

        );

    }

    // ======================================
    // ATUALIZAR HISTÓRICO
    // ======================================

    if (render) {

        renderHistory();

    }

}


// ==========================================
// TIPOS DE REGISTRO
// ==========================================

function getTypeClass(caption) {

    if (caption.importante) {

        return "important";

    }

    const classes = {

        conteudo: "content",

        atividade: "activity",

        trabalho: "work"

    };

    return classes[caption.tipo] || "content";

}


function getTypeLabel(caption) {

    if (caption.importante) {

        return "Importante";

    }

    const labels = {

        conteudo: "Conteúdo",

        atividade: "Atividade",

        trabalho: "Trabalho"

    };

    return labels[caption.tipo] || "Conteúdo";

}


// ==========================================
// HISTÓRICO
// ==========================================

function renderHistory() {

    elements.history.replaceChildren();

    const filtered = state.history.filter(

        caption => {

            if (state.filter === "todos") {

                return true;

            }

            if (state.filter === "importante") {

                return caption.importante;

            }

            return caption.tipo === state.filter;

        }

    );

    // ======================================
    // HISTÓRICO VAZIO
    // ======================================

    if (!filtered.length) {

        const message = document.createElement(
            "p"
        );

        message.className =
            "empty-message";

        message.textContent =

            "Nenhuma transcrição disponível.";

        elements.history.appendChild(
            message
        );

        return;

    }

    // ======================================
    // CRIAR REGISTROS
    // ======================================

    const fragment =
        document.createDocumentFragment();

    filtered.forEach(caption => {

        const article = document.createElement(
            "article"
        );

        article.className =

            `history-item ${getTypeClass(caption)}`;

        // Metadados do registro.

        const meta = document.createElement(
            "div"
        );

        meta.className =
            "history-meta";

        // Tipo.

        const type = document.createElement(
            "span"
        );

        type.textContent =

            getTypeLabel(caption);

        // Horário.

        const time = document.createElement(
            "time"
        );

        time.textContent =

            formatTime(caption.horario);

        time.dateTime =
            caption.horario;

        // Texto definitivo.

        const text = document.createElement(
            "p"
        );

        text.className =
            "history-text";

        text.textContent =
            caption.texto;

        // Montagem.

        meta.append(

            type,

            time

        );

        article.append(

            meta,

            text

        );

        fragment.appendChild(
            article
        );

    });

    elements.history.appendChild(
        fragment
    );

    scrollHistory();

}


// ==========================================
// ROLAGEM DO HISTÓRICO
// ==========================================

function scrollHistory() {

    if (!state.autoScroll) {

        return;

    }

    elements.history.scrollTop =

        elements.history.scrollHeight;

}


// ==========================================
// LIMPAR HISTÓRICO LOCAL
// ==========================================

function clearHistory() {

    // Limpa somente a visualização do aluno.
    //
    // Não apaga as transcrições do servidor.
    // Também mantém os IDs já recebidos para
    // evitar que os mesmos registros retornem
    // após uma reconexão.

    state.history = [];

    renderHistory();

}


// ==========================================
// FILTROS
// ==========================================

function selectFilter(filter) {

    state.filter = filter;

    document.querySelectorAll(

        ".filter"

    ).forEach(button => {

        const selected =

            button.dataset.filter === filter;

        button.classList.toggle(

            "active",

            selected

        );

        button.setAttribute(

            "aria-pressed",

            String(selected)

        );

    });

    renderHistory();

}


// ==========================================
// INFORMAÇÕES IMPORTANTES
// ==========================================

function addImportant(text) {

    const normalized =
        normalizeText(text);

    if (!normalized) {

        return;

    }

    // Evita repetir a mesma informação.

    const alreadyExists = Array.from(

        elements.importantContent.children

    ).some(

        item => item.textContent === normalized

    );

    if (alreadyExists) {

        return;

    }

    elements.importantPanel.hidden = false;

    const item = document.createElement(
        "p"
    );

    item.className =
        "important-item";

    item.textContent =
        normalized;

    elements.importantContent.appendChild(
        item
    );

}


// ==========================================
// INDICADOR DE TRANSMISSÃO
// ==========================================

function setLiveStatus(active, text) {

    const indicator = document.querySelector(

        ".live-indicator"

    );

    if (indicator) {

        indicator.classList.toggle(

            "active",

            active

        );

    }

    elements.liveText.textContent =
        text;

}


// ==========================================
// FINALIZAR AULA
// ==========================================

function finishLesson(data) {

    const id =
        data.id || data.aula_id || null;

    if (

        id

        &&

        state.lessonId

        &&

        id !== state.lessonId

    ) {

        return;

    }

    // ======================================
    // REGISTRAR HORÁRIO FINAL
    // ======================================

    state.lessonEnd =

        data.fim

        ||

        new Date().toISOString();

    clearPartialCaption();

    updateLessonState(
        "finalizado"
    );

    elements.lessonSubtitle.textContent =

        "A aula foi encerrada.";

    // ======================================
    // RECUPERAR REGISTROS FINAIS
    // ======================================

    if (Array.isArray(data.registros)) {

        for (const record of data.registros) {

            receiveCaption(

                record,

                {

                    render: false,

                    announce: false

                }

            );

        }

        renderHistory();

    }

    setLiveStatus(

        false,

        "Aula finalizada"

    );

    // ======================================
    // PROCESSAMENTO DO MATERIAL
    // ======================================

    showProcessing(

        "Processando aula",

        "O agente está preparando o material "

        + "de estudo. Você poderá recebê-lo por e-mail."

    );

    updateTimer();

}


// ==========================================
// PAINEL DE PROCESSAMENTO
// ==========================================

function showProcessing(title, message) {

    state.processing = {

        estado: "processando",

        titulo: title,

        mensagem: message

    };

    elements.processingPanel.hidden = false;

    elements.processingIcon.textContent = "...";

    elements.processingTitle.textContent =
        title;

    elements.processingMessage.textContent =
        message;

}


// ==========================================
// PROCESSAMENTO CONCLUÍDO
// ==========================================

function showCompleted(title, message) {

    state.processing = {

        estado: "concluido",

        titulo: title,

        mensagem: message

    };

    elements.processingPanel.hidden = false;

    elements.processingIcon.textContent = "✓";

    elements.processingTitle.textContent =
        title;

    elements.processingMessage.textContent =
        message;

}


// ==========================================
// ERRO DE PROCESSAMENTO
// ==========================================

function showError(message) {

    state.processing = {

        estado: "erro",

        titulo: "Falha no processamento",

        mensagem: message

    };

    elements.processingPanel.hidden = false;

    elements.processingIcon.textContent = "!";

    elements.processingTitle.textContent =

        "Falha no processamento";

    elements.processingMessage.textContent =
        message;

}


// ==========================================
// FORMATAÇÃO DE HORÁRIO
// ==========================================

function formatTime(value) {

    const date = new Date(
        value
    );

    if (Number.isNaN(date.getTime())) {

        return "--:--:--";

    }

    return date.toLocaleTimeString(

        "pt-BR",

        {

            hour: "2-digit",

            minute: "2-digit",

            second: "2-digit"

        }

    );

}


// ==========================================
// CRONÔMETRO DA AULA
// ==========================================

function updateTimer() {

    if (!state.lessonStart) {

        elements.timer.textContent =

            "00:00:00";

        return;

    }

    const start = new Date(

        state.lessonStart

    ).getTime();

    const end = state.lessonEnd

        ? new Date(state.lessonEnd).getTime()

        : Date.now();

    if (

        Number.isNaN(start)

        ||

        Number.isNaN(end)

    ) {

        return;

    }

    const seconds = Math.max(

        0,

        Math.floor(

            (end - start) / 1000

        )

    );

    const hours = Math.floor(

        seconds / 3600

    );

    const minutes = Math.floor(

        (seconds % 3600) / 60

    );

    const remainingSeconds =

        seconds % 60;

    elements.timer.textContent =

        [

            hours,

            minutes,

            remainingSeconds

        ]

        .map(

            value => String(value).padStart(

                2,

                "0"

            )

        )

        .join(":");

}


// ==========================================
// EVENTOS DOS BOTÕES
// ==========================================

elements.fontDecrease.addEventListener(

    "click",

    () => changeFontSize(

        -CONFIG.fontStep

    )

);


elements.fontIncrease.addEventListener(

    "click",

    () => changeFontSize(

        CONFIG.fontStep

    )

);


elements.contrastToggle.addEventListener(

    "click",

    toggleContrast

);


elements.fullscreenToggle.addEventListener(

    "click",

    toggleFullscreen

);


elements.pauseToggle.addEventListener(

    "click",

    toggleAutoScroll

);


elements.clearHistory.addEventListener(

    "click",

    clearHistory

);


// ==========================================
// BOTÕES DOS FILTROS
// ==========================================

document.querySelectorAll(

    ".filter"

).forEach(button => {

    button.addEventListener(

        "click",

        () => selectFilter(

            button.dataset.filter

        )

    );

});


// ==========================================
// RECONECTAR QUANDO A INTERNET VOLTAR
// ==========================================

window.addEventListener(

    "online",

    () => {

        if (!state.connected) {

            connectWebSocket();

        }

    }

);


window.addEventListener(

    "offline",

    () => {

        updateConnection(

            "disconnected"

        );

        if (state.socket) {

            try {

                state.socket.close();

            } catch (error) {

                console.warn(error);

            }

        }

        scheduleReconnect();

    }

);


// ==========================================
// RECONECTAR AO RETORNAR PARA A PÁGINA
// ==========================================

document.addEventListener(

    "visibilitychange",

    () => {

        if (

            document.visibilityState === "visible"

            &&

            !state.connected

        ) {

            connectWebSocket();

        }

    }

);


// ==========================================
// INICIALIZAÇÃO
// ==========================================

function initialize() {

    console.log(

        "[AGENTE IHC] Interface do aluno inicializada."

    );

    console.log(

        "[AGENTE IHC] Compatível com HTTP e HTTPS."

    );

    console.log(

        "[AGENTE IHC] Legendas Vosk + Whisper."

    );

    loadPreferences();

    applyPreferences();

    renderHistory();

    updateTimer();

    setInterval(

        updateTimer,

        1000

    );

    connectWebSocket();

}


initialize();