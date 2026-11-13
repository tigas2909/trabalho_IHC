
#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "========================================="
echo " Instalando Agente de Acessibilidade"
echo "========================================="

# Dependencias do sistema
sudo apt update

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    git \
    adb

# Ambiente virtual
echo "Criando ambiente virtual..."

python3 -m venv .venv

source .venv/bin/activate

# Dependencias Python
echo "Instalando bibliotecas Python..."

python -m pip install --upgrade pip

python -m pip install -r install.txt

# Diretorios necessarios
mkdir -p dados/transcricoes
mkdir -p dados/relatorios
mkdir -p modelos

# Configuracoes
if [ ! -f .env ]; then
    touch .env
fi

echo "========================================="
echo " Instalacao concluida!"
echo "========================================="
