#!/bin/bash

# Script para configurar a VM no Google Cloud (Ubuntu/Debian)

echo "--- Iniciando configuração da VM bairro-seguro-backend ---"

# 1. Atualizar o sistema
sudo apt-get update
sudo apt-get upgrade -y

# 2. Instalar Docker
echo "--- Instalando Docker ---"
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 3. Adicionar o usuário ao grupo docker para não precisar usar sudo
sudo usermod -aG docker $USER

echo "--- Docker instalado com sucesso! ---"
echo "OBS: Você precisará sair e entrar novamente na VM para usar o docker sem sudo."

# 4. Instruções Finais
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Clone seu repositório: git clone <seu-repo-url>"
echo "2. Entre na pasta: cd bairro-seguro-api"
echo "3. Crie o arquivo .env: cp .env.example .env"
echo "4. Edite o .env com suas configurações: nano .env"
echo "5. Inicie a API: docker compose up -d --build"
echo ""
echo "API estará rodando na porta 8000 (lembre-se de abrir a porta 8000 no firewall do GCP)"
