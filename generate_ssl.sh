#!/bin/bash

# Script para gerar certificado SSL autoassinado para IP

echo "--- Gerando Certificado SSL Autoassinado ---"

# Detecta o IP externo da VM (funciona no GCP)
EXTERNAL_IP=$(curl -s ifconfig.me)

if [ -z "$EXTERNAL_IP" ]; then
    echo "Não foi possível detectar o IP externo automaticamente."
    read -p "Digite o IP do servidor: " EXTERNAL_IP
fi

echo "IP detectado: $EXTERNAL_IP"

# Cria o diretório para os certificados
mkdir -p ./nginx/ssl

# Gera a chave privada e o certificado
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/nginx-selfsigned.key \
  -out ./nginx/ssl/nginx-selfsigned.crt \
  -subj "/C=BR/ST=SP/L=SaoPaulo/O=BairroSeguro/OU=API/CN=$EXTERNAL_IP" \
  -addext "subjectAltName=IP:$EXTERNAL_IP"

# Define permissões adequadas
chmod 600 ./nginx/ssl/nginx-selfsigned.key
chmod 644 ./nginx/ssl/nginx-selfsigned.crt

echo ""
echo "✅ Certificado SSL gerado com sucesso!"
echo "   - Certificado: ./nginx/ssl/nginx-selfsigned.crt"
echo "   - Chave: ./nginx/ssl/nginx-selfsigned.key"
echo "   - IP configurado: $EXTERNAL_IP"
echo ""
echo "⚠️  ATENÇÃO: Este é um certificado autoassinado."
echo "   Os navegadores exibirão um aviso de segurança."
echo "   Para produção, considere usar um domínio + Let's Encrypt."
echo ""
