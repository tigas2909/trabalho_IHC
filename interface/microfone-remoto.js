"use strict";

// ==========================================
// SESSÃO DO MICROFONE
// ==========================================

let sessaoMicrofone = null;

let iniciandoMicrofone = false;

// ==========================================
// STATUS
// ==========================================

function mostrarStatusAudio(
    texto,
    erro = false
) {

    const campo = document.getElementById(
        "statusRemoto"
    );

    if (campo) {

        campo.textContent = texto;

        campo.classList.toggle(
            "erro",
            erro
        );

    }

    console.log(
        "[MICROFONE REMOTO]",
        texto
    );

}

function microfoneRemotoOcupado() {

    return Boolean(
        iniciandoMicrofone
        || sessaoMicrofone
    );

}

// ==========================================
// ATUALIZAR MEDIDOR
// ==========================================

function atualizarNivelAudio(volume) {

    const medidor = (
        document.getElementById(
            "nivelAudio"
        )
    );

    if (!medidor) {
        return;
    }

    const nivel = Math.min(

        100,

        Math.max(
            0,
            volume * 350
        )

    );

    medidor.style.width = (
        nivel + "%"
    );

}

// ==========================================
// CONFERIR SESSÃO
// ==========================================

function sessaoAtiva(sessao) {

    return (

        sessaoMicrofone === sessao

        && !sessao.cancelada

    );

}

// ==========================================
// ENCERRAR RECURSOS
// ==========================================

async function limparSessao(sessao) {

    if (!sessao) {
        return;
    }

    sessao.cancelada = true;

    if (sessao.processador) {

        sessao.processador.port.onmessage = null;

        try {

            sessao.processador.disconnect();

        } catch {

            // Já desconectado.

        }

        sessao.processador = null;

    }

    if (sessao.fonte) {

        try {

            sessao.fonte.disconnect();

        } catch {

            // Já desconectado.

        }

        sessao.fonte = null;

    }

    if (sessao.saidaSilenciosa) {

        try {

            sessao.saidaSilenciosa.disconnect();

        } catch {

            // Já desconectado.

        }

        sessao.saidaSilenciosa = null;

    }

    if (sessao.stream) {

        for (
            const faixa
            of sessao.stream.getTracks()
        ) {

            faixa.stop();

        }

        sessao.stream = null;

    }

    if (sessao.socket) {

        const socket = sessao.socket;

        sessao.socket = null;

        socket.onclose = null;

        socket.onerror = null;

        socket.onmessage = null;

        if (

            socket.readyState
            === WebSocket.OPEN

            || socket.readyState
            === WebSocket.CONNECTING

        ) {

            try {

                socket.close();

            } catch {

                // Conexão já encerrada.

            }

        }

    }

    if (sessao.contexto) {

        const contexto = (
            sessao.contexto
        );

        sessao.contexto = null;

        if (
            contexto.state !== "closed"
        ) {

            try {

                await contexto.close();

            } catch {

                // Contexto já encerrado.

            }

        }

    }

    atualizarNivelAudio(0);

}

// ==========================================
// AGUARDAR SERVIDOR
// ==========================================

function aguardarServidor(sessao) {

    return new Promise(
        (resolve, reject) => {

            const socket = sessao.socket;

            let terminou = false;

            function concluir(
                erro = null
            ) {

                if (terminou) {
                    return;
                }

                terminou = true;

                clearTimeout(timeout);

                socket.removeEventListener(
                    "message",
                    aoMensagem
                );

                socket.removeEventListener(
                    "close",
                    aoFechar
                );

                socket.removeEventListener(
                    "error",
                    aoErro
                );

                if (erro) {

                    reject(erro);

                } else {

                    resolve();

                }

            }

            function aoMensagem(evento) {

                let dados;

                try {

                    dados = JSON.parse(
                        evento.data
                    );

                } catch {

                    return;

                }

                if (
                    dados.evento === "carregando"
                ) {

                    mostrarStatusAudio(

                        dados.mensagem

                        || "Carregando modelos..."

                    );

                }

                if (
                    dados.evento === "pronto"
                ) {

                    concluir();

                }

                if (
                    dados.evento === "erro"
                ) {

                    concluir(

                        new Error(

                            dados.mensagem

                            || "Erro no servidor."

                        )

                    );

                }

            }

            function aoFechar(evento) {

                concluir(

                    new Error(

                        "Conexão recusada ou encerrada. "
                        + "Código: "
                        + evento.code

                    )

                );

            }

            function aoErro() {

                concluir(

                    new Error(

                        "Falha ao conectar ao servidor."

                    )

                );

            }

            const timeout = setTimeout(

                () => concluir(

                    new Error(

                        "Tempo limite aguardando "
                        + "Vosk e Whisper."

                    )

                ),

                40000

            );

            socket.addEventListener(

                "message",

                aoMensagem

            );

            socket.addEventListener(

                "close",

                aoFechar

            );

            socket.addEventListener(

                "error",

                aoErro

            );

        }
    );

}

// ==========================================
// INICIAR MICROFONE DO CELULAR
// ==========================================

async function iniciarMicrofoneRemoto() {

    if (
        iniciandoMicrofone
        || sessaoMicrofone
    ) {

        return;

    }

    iniciandoMicrofone = true;

    const sessao = {

        cancelada: false,

        socket: null,

        contexto: null,

        stream: null,

        fonte: null,

        processador: null,

        saidaSilenciosa: null

    };

    sessaoMicrofone = sessao;

    try {

        // ==================================
        // VERIFICAR HTTPS
        // ==================================

        if (!window.isSecureContext) {

            throw new Error(

                "O navegador exige HTTPS "
                + "confiável para acessar "
                + "o microfone."

            );

        }

        if (

            window.location.protocol
            !== "https:"

        ) {

            throw new Error(

                "Abra o painel utilizando HTTPS."

            );

        }

        if (

            !navigator.mediaDevices

            || !navigator.mediaDevices.getUserMedia

        ) {

            throw new Error(

                "O navegador não permite "
                + "acessar o microfone."

            );

        }

        // ==================================
        // CRIAR CONTEXTO DE ÁUDIO
        // ==================================

        const AudioContextClass = (

            window.AudioContext

            || window.webkitAudioContext

        );

        if (!AudioContextClass) {

            throw new Error(

                "AudioContext não está disponível."

            );

        }

        sessao.contexto = (
            new AudioContextClass()
        );

        await sessao.contexto.resume();

        // ==================================
        // SOLICITAR MICROFONE
        // ==================================

        mostrarStatusAudio(

            "Solicitando acesso "
            + "ao microfone do celular..."

        );

        const stream = (

            await navigator.mediaDevices.getUserMedia({

                audio: {

                    channelCount: {
                        ideal: 1
                    },

                    echoCancellation: true,

                    noiseSuppression: true,

                    autoGainControl: true

                },

                video: false

            })

        );

        // Se o usuário cancelou enquanto
        // o navegador solicitava permissão.

        if (!sessaoAtiva(sessao)) {

            for (
                const faixa
                of stream.getTracks()
            ) {

                faixa.stop();

            }

            return;

        }

        sessao.stream = stream;

        for (
            const faixa
            of stream.getAudioTracks()
        ) {

            faixa.addEventListener(

                "ended",

                () => {

                    if (
                        sessaoAtiva(sessao)
                    ) {

                        pararMicrofoneRemoto(

                            "O dispositivo de áudio "
                            + "foi desconectado.",

                            true

                        );

                    }

                }

            );

        }

        // ==================================
        // CONFERIR FREQUÊNCIA DE ÁUDIO
        // ==================================

        if (
            sessao.contexto.sampleRate < 16000
        ) {

            throw new Error(

                "A frequência de áudio do "
                + "dispositivo é inferior a 16 kHz."

            );

        }

        if (
            !sessao.contexto.audioWorklet
        ) {

            throw new Error(

                "O navegador não suporta "
                + "AudioWorklet."

            );

        }

        // ==================================
        // CARREGAR CONVERSOR PCM
        // ==================================

        await sessao.contexto.audioWorklet.addModule(

            "/audio-processor.js"

        );

        if (!sessaoAtiva(sessao)) {
            return;
        }

        sessao.fonte = (

            sessao.contexto.createMediaStreamSource(

                sessao.stream

            )

        );

        sessao.processador = (

            new AudioWorkletNode(

                sessao.contexto,

                "captura-audio",

                {

                    numberOfInputs: 1,

                    numberOfOutputs: 1,

                    outputChannelCount: [1]

                }

            )

        );

        // ==================================
        // CONECTAR WEBSOCKET SEGURO
        // ==================================

        mostrarStatusAudio(

            "Conectando ao servidor..."

        );

        const endereco = new URL(

            "/ws/professor/audio",

            window.location.href

        );

        endereco.protocol = "wss:";

        sessao.socket = new WebSocket(

            endereco.toString()

        );

        sessao.socket.binaryType = "arraybuffer";

        // Não transmite áudio enquanto
        // os modelos ainda estão carregando.

        await aguardarServidor(sessao);

        if (!sessaoAtiva(sessao)) {
            return;
        }

        // ==================================
        // EVENTOS DO SERVIDOR
        // ==================================

        sessao.socket.onclose = evento => {

            if (
                sessaoAtiva(sessao)
            ) {

                pararMicrofoneRemoto(

                    "Conexão de áudio encerrada. "
                    + "Código: "
                    + evento.code,

                    evento.code !== 1000

                );

            }

        };

        sessao.socket.onerror = () => {

            if (
                sessaoAtiva(sessao)
            ) {

                pararMicrofoneRemoto(

                    "Erro na transmissão de áudio.",

                    true

                );

            }

        };

        sessao.socket.onmessage = evento => {

            let dados;

            try {

                dados = JSON.parse(
                    evento.data
                );

            } catch {

                return;

            }

            if (
                dados.evento === "erro"
            ) {

                pararMicrofoneRemoto(

                    dados.mensagem

                    || "Erro no reconhecimento.",

                    true

                );

            }

        };

        // ==================================
        // ENVIAR ÁUDIO PARA O PYTHON
        // ==================================

        sessao.processador.port.onmessage = evento => {

            if (!sessaoAtiva(sessao)) {
                return;
            }

            if (

                !sessao.socket

                || sessao.socket.readyState
                !== WebSocket.OPEN

            ) {

                return;

            }

            const audio = evento.data.audio;

            const volume = (
                evento.data.volume || 0
            );

            atualizarNivelAudio(volume);

            // Impede crescimento ilimitado
            // do buffer de transmissão.

            if (

                sessao.socket.bufferedAmount

                > 256000

            ) {

                pararMicrofoneRemoto(

                    "Rede sobrecarregada. "
                    + "Transmissão interrompida.",

                    true

                );

                return;

            }

            if (
                audio instanceof ArrayBuffer
            ) {

                sessao.socket.send(audio);

            }

        };

        // ==================================
        // SAÍDA SILENCIOSA
        // ==================================

        sessao.saidaSilenciosa = (

            sessao.contexto.createGain()

        );

        sessao.saidaSilenciosa.gain.value = 0;

        sessao.fonte.connect(

            sessao.processador

        );

        sessao.processador.connect(

            sessao.saidaSilenciosa

        );

        sessao.saidaSilenciosa.connect(

            sessao.contexto.destination

        );

        await sessao.contexto.resume();

        mostrarStatusAudio(

            "Microfone conectado! "
            + "Pode falar."

        );

        if (
            typeof feedback === "function"
        ) {

            feedback(

                "Microfone do celular conectado."

            );

        }

        if (
            typeof atualizarStatus
            === "function"
        ) {

            await atualizarStatus();

        }

    } catch (erro) {

        if (
            sessaoAtiva(sessao)
        ) {

            sessaoMicrofone = null;

            await limparSessao(sessao);

            let mensagem = erro.message;

            if (
                erro.name === "NotAllowedError"
            ) {

                mensagem = (

                    "Permissão de microfone negada. "
                    + "Verifique as permissões "
                    + "do navegador."

                );

            } else if (
                erro.name === "NotFoundError"
            ) {

                mensagem = (

                    "Nenhum microfone foi "
                    + "encontrado neste dispositivo."

                );

            } else if (
                erro.name === "NotReadableError"
            ) {

                mensagem = (

                    "Não foi possível acessar "
                    + "o microfone. Verifique se "
                    + "outro aplicativo está usando."

                );

            }

            mostrarStatusAudio(

                mensagem,

                true

            );

            if (
                typeof feedback === "function"
            ) {

                feedback(

                    mensagem,

                    true

                );

            }

        }

    } finally {

        iniciandoMicrofone = false;

    }

}

// ==========================================
// PARAR MICROFONE REMOTO
// ==========================================

async function pararMicrofoneRemoto(

    mensagem = "Microfone do celular desligado.",

    erro = false

) {

    const sessao = sessaoMicrofone;

    sessaoMicrofone = null;

    await limparSessao(sessao);

    mostrarStatusAudio(

        mensagem,

        erro

    );

    if (
        typeof atualizarStatus
        === "function"
    ) {

        await atualizarStatus();

    }

}

// ==========================================
// ENCERRAR AO SAIR DA PÁGINA
// ==========================================

window.addEventListener(

    "pagehide",

    () => {

        pararMicrofoneRemoto();

    }

);