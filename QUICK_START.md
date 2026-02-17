# 🚀 Guia Rápido - Deploy com SSL

## Para testar localmente (sem SSL):
```bash
docker compose up -d --build
# Acesse: http://localhost
```

## Para deploy na VM do GCP (com SSL):

### 1️⃣ Na VM, execute:
```bash
# Setup inicial (apenas primeira vez)
./setup_gcp_vm.sh

# Clone e configure
git clone <seu-repo>
cd bairro-seguro-api
cp .env.example .env
nano .env

# Gere certificado SSL
./generate_ssl.sh

# Inicie a aplicação
docker compose up -d --build
```

### 2️⃣ No Console GCP, abra as portas:
```bash
gcloud compute firewall-rules create allow-http --allow tcp:80 --source-ranges 0.0.0.0/0
gcloud compute firewall-rules create allow-https --allow tcp:443 --source-ranges 0.0.0.0/0
```

### 3️⃣ Acesse:
```
https://<IP-DA-VM>
```

## Comandos úteis:
```bash
# Ver logs
docker compose logs -f

# Reiniciar
docker compose restart

# Parar
docker compose down

# Rebuild completo
docker compose down && docker compose up -d --build

# Regenerar SSL
./generate_ssl.sh && docker compose restart nginx
```

## ⚠️ Lembre-se:
- Certificado autoassinado = aviso no navegador (normal!)
- Para produção: use domínio + Let's Encrypt
- Veja `SSL_SETUP.md` para detalhes completos
