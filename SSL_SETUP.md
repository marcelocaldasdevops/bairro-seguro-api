# 🔒 Configuração SSL para Bairro Seguro API

Este guia explica como configurar HTTPS (SSL/TLS) para a API usando certificado autoassinado.

## 📋 Pré-requisitos

- VM no Google Cloud (ou qualquer servidor Linux)
- Docker e Docker Compose instalados
- Portas 80 e 443 abertas no firewall

## 🚀 Configuração Rápida

### 1. Execute o script de setup da VM

```bash
chmod +x setup_gcp_vm.sh
./setup_gcp_vm.sh
```

### 2. Clone o repositório e configure

```bash
git clone <seu-repositorio>
cd bairro-seguro-api
cp .env.example .env
nano .env  # Configure suas variáveis de ambiente
```

### 3. Gere o certificado SSL

```bash
chmod +x generate_ssl.sh
./generate_ssl.sh
```

O script irá:
- Detectar automaticamente o IP externo da VM
- Gerar um certificado autoassinado válido por 365 dias
- Criar os arquivos em `./nginx/ssl/`

### 4. Inicie a aplicação

```bash
docker compose up -d --build
```

### 5. Configure o Firewall do GCP

No console do Google Cloud:

1. Vá em **VPC Network** → **Firewall**
2. Crie uma regra para **HTTP** (porta 80):
   - Nome: `allow-http`
   - Destinos: `Todas as instâncias na rede`
   - Filtro de origem: `0.0.0.0/0`
   - Protocolos e portas: `tcp:80`

3. Crie uma regra para **HTTPS** (porta 443):
   - Nome: `allow-https`
   - Destinos: `Todas as instâncias na rede`
   - Filtro de origem: `0.0.0.0/0`
   - Protocolos e portas: `tcp:443`

Ou via CLI:

```bash
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic"

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic"
```

## 🌐 Acessando a API

Acesse via HTTPS:
```
https://<IP-DA-VM>
```

**⚠️ IMPORTANTE:** Como o certificado é autoassinado, o navegador exibirá um aviso de segurança. Clique em "Avançado" e "Continuar para o site (inseguro)".

## 🔄 Comportamento

- **HTTP (porta 80)**: Redireciona automaticamente para HTTPS
- **HTTPS (porta 443)**: Serve a API com SSL

## 📝 Arquivos Modificados

- `nginx/default.conf` - Configuração do Nginx com SSL
- `docker-compose.yml` - Expõe porta 443 e monta certificados
- `generate_ssl.sh` - Script de geração de certificados
- `setup_gcp_vm.sh` - Instalação automatizada

## 🔐 Segurança

### Certificado Autoassinado (Desenvolvimento/Interno)

✅ **Vantagens:**
- Grátis e rápido
- Funciona com IPs
- Ideal para desenvolvimento e uso interno

❌ **Desvantagens:**
- Avisos de segurança no navegador
- Não é confiável publicamente
- Requer aceitar manualmente o certificado

### Para Produção (Recomendado)

Para um ambiente de produção, use um **domínio real** + **Let's Encrypt**:

1. **Compre um domínio** (ex: `api.bairroseguro.com.br`)
2. **Aponte o DNS** para o IP da VM
3. **Use Certbot** para gerar certificado gratuito:

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Gerar certificado (substitua pelo seu domínio)
sudo certbot --nginx -d api.bairroseguro.com.br

# Renovação automática
sudo certbot renew --dry-run
```

## 🛠️ Troubleshooting

### Erro: "Connection refused"
- Verifique se o Docker está rodando: `docker compose ps`
- Verifique se as portas estão abertas: `sudo netstat -tlnp | grep -E '80|443'`

### Erro: "SSL certificate problem"
- Normal para certificados autoassinados
- No navegador: aceite o certificado manualmente
- Em APIs (curl): use `curl -k https://...` (não recomendado em produção)

### Regenerar certificado

```bash
./generate_ssl.sh
docker compose restart nginx
```

## 📚 Referências

- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
