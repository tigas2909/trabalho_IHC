"use strict";

class CapturaAudioProcessor extends AudioWorkletProcessor {

    constructor() {

        super();

        this.taxaDestino = 16000;

        this.fase = 0;

        this.soma = 0;

        this.quantidade = 0;

        this.tamanhoBloco = 4000;

        this.buffer = new ArrayBuffer(
            this.tamanhoBloco * 2
        );

        this.visao = new DataView(
            this.buffer
        );

        this.posicao = 0;

        this.somaQuadrados = 0;

        this.totalVolume = 0;

    }

    // ======================================
    // ADICIONAR AMOSTRA
    // ======================================

    adicionarAmostra(amostra) {

        amostra = Math.max(
            -1,
            Math.min(1, amostra)
        );

        const pcm = amostra < 0

            ? Math.round(amostra * 32768)

            : Math.round(amostra * 32767);

        // PCM signed int16 little-endian.

        this.visao.setInt16(
            this.posicao * 2,
            pcm,
            true
        );

        this.posicao++;

        this.somaQuadrados += (
            amostra * amostra
        );

        this.totalVolume++;

        // ==================================
        // ENVIAR BLOCO COMPLETO
        // ==================================

        if (
            this.posicao
            >= this.tamanhoBloco
        ) {

            const rms = Math.sqrt(

                this.somaQuadrados

                / Math.max(
                    1,
                    this.totalVolume
                )

            );

            this.port.postMessage(

                {
                    audio: this.buffer,
                    volume: rms
                },

                [this.buffer]

            );

            this.buffer = new ArrayBuffer(
                this.tamanhoBloco * 2
            );

            this.visao = new DataView(
                this.buffer
            );

            this.posicao = 0;

            this.somaQuadrados = 0;

            this.totalVolume = 0;

        }

    }

    // ======================================
    // PROCESSAR ÁUDIO
    // ======================================

    process(inputs, outputs) {

        const entrada = inputs[0];

        const saida = outputs[0];

        // O áudio não deve ser reproduzido
        // no próprio celular.

        if (saida) {

            for (const canal of saida) {

                canal.fill(0);

            }

        }

        if (
            !entrada
            || !entrada[0]
            || entrada[0].length === 0
        ) {

            return true;

        }

        const tamanho = entrada[0].length;

        const quantidadeCanais = entrada.length;

        for (
            let i = 0;
            i < tamanho;
            i++
        ) {

            // Converter para mono.

            let amostra = 0;

            for (
                let canal = 0;
                canal < quantidadeCanais;
                canal++
            ) {

                amostra += entrada[canal][i];

            }

            amostra /= quantidadeCanais;

            // Reduzir a frequência de amostragem.

            this.soma += amostra;

            this.quantidade++;

            this.fase += this.taxaDestino;

            if (
                this.fase >= sampleRate
            ) {

                this.fase -= sampleRate;

                const convertida = (

                    this.soma

                    / this.quantidade

                );

                this.adicionarAmostra(
                    convertida
                );

                this.soma = 0;

                this.quantidade = 0;

            }

        }

        return true;

    }

}

// ==========================================
// REGISTRAR PROCESSADOR
// ==========================================

registerProcessor(

    "captura-audio",

    CapturaAudioProcessor

);