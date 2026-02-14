# Bairro Seguro Cloud

Plataforma colaborativa de segurança para conectar moradores e reportar incidentes em tempo real.

## Stack Tecnológico
- **Backend:** Python + Django + Django Rest Framework
- **Frontend:** Angular 16 + Vanilla CSS (Premium Design)
- **Banco de Dados:** PostgreSQL
- **Infraestrutura:** Docker, Kubernetes
- **CI/CD:** GitHub Actions

## Como Executar Localmente

### Usando Docker (Recomendado)
Execute os seguintes comandos na raiz do projeto:
```bash
docker-compose up --build
```
O backend estará disponível em `http://localhost:8000` e o frontend em `http://localhost:4200`.

### Sem Docker

#### Backend
1. Entre na pasta `backend`: `cd backend`
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute as migrações: `python manage.py migrate`
4. Inicie o servidor: `python manage.py runserver`

#### Frontend
1. Entre na pasta `frontend`: `cd frontend`
2. Instale as dependências: `npm install`
3. Inicie o servidor: `npm start`

## Funcionalidades
1. **Cadastro Simples:** Permite criar conta apenas com usuário, e-mail e senha.
2. **Perfil Completo:** Para relatar incidentes, o usuário deve completar seu perfil (Nome, CPF e Bairro).
3. **Relato de Incidentes:** Compartilhamento de incidentes com descrição, nível de gravidade e localização.
4. **Dashboard:** Visualização de todos os incidentes relatados no bairro.

## Estrutura do Projeto
- `/backend`: API REST desenvolvida em Django.
- `/frontend`: Aplicação Angular com design premium e responsivo.
- `/k8s`: Manifestos Kubernetes para deploy em larga escala.
- `.github/workflows`: Pipeline de CI/CD para automação de testes e build.
