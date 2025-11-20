# Middleware de Integração WhatsApp - MVP

Middleware de integração entre o Portal de Licenças (CCD) e a WhatsApp Cloud API (Meta) para envio de mensagens segmentadas baseadas no tipo de licença.

## 🚀 Funcionalidades

- **Importação CSV**: Upload e processamento de arquivos CSV com dados de clientes
- **Segmentação**: Classificação automática de clientes por tipo de licença (Start ou Hub)
- **Mensagens Massivas**: Envio de HSMs personalizadas via WhatsApp Cloud API
- **Webhooks**: Recebimento de eventos `licenca-criada` do Portal de Licenças
- **Boas-vindas Automáticas**: Disparo automático de mensagens de boas-vindas segmentadas

## 📋 Pré-requisitos

- Python 3.10+
- MongoDB Atlas (recomendado) ou MongoDB local 4.4+
- Conta na WhatsApp Cloud API (Meta)

## 🔧 Instalação

### Opção 1: Usando Makefile (Recomendado)

1. Clone o repositório:
```bash
git clone <repository-url>
cd whatsapp-middleware
```

2. Prepare o ambiente (cria venv, instala dependências e configura .env):
```bash
make setup
```

3. Execute o projeto:
```bash
make run
```

### Opção 2: Instalação Manual

1. Clone o repositório:
```bash
git clone <repository-url>
cd whatsapp-middleware
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env na raiz do projeto com suas credenciais:
# - MongoDB (MONGODB_URL, MONGODB_DB_NAME)
# - WhatsApp Cloud API (WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_VERIFY_TOKEN)
# - Configurações da aplicação (API_HOST, API_PORT, ENVIRONMENT)
```

**Nota:** O arquivo `.env` deve estar na raiz do projeto e será carregado automaticamente pela aplicação.

**MongoDB Atlas:** Se você está usando MongoDB Atlas, consulte o [GUIA_MONGODB_ATLAS.md](GUIA_MONGODB_ATLAS.md) para configuração detalhada.

## 🏃 Executando a Aplicação

### Com Makefile:
```bash
make run          # Modo desenvolvimento (com reload)
make run-prod     # Modo produção
```

### Manualmente:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A aplicação estará disponível em `http://localhost:8000`

## 🛠️ Comandos Makefile

### Linux/Mac:
Execute `make help` para ver todos os comandos disponíveis:

```bash
make setup        # Prepara o ambiente completo
make run          # Executa o projeto
make test         # Executa os testes
make test-cov     # Testes com cobertura
make clean        # Limpa arquivos temporários
make docker-up    # Inicia MongoDB via Docker
make dev          # Setup + executa (atalho)
```

### Windows:
Use `make.bat` com os mesmos comandos:

```cmd
make.bat setup    # Prepara o ambiente completo
make.bat run      # Executa o projeto
make.bat test     # Executa os testes
make.bat help     # Mostra ajuda
```

Para mais informações, consulte o Makefile ou execute `make help` (Linux/Mac) / `make.bat help` (Windows).

## 📚 Documentação da API

Após iniciar a aplicação, acesse:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testes

### Com Makefile:
```bash
make test         # Executa todos os testes
make test-cov     # Testes com relatório de cobertura
```

### Manualmente:
```bash
pytest
pytest --cov=app --cov-report=html
```

O relatório de cobertura será gerado em `htmlcov/index.html`

## 📖 Documentação Completa

Consulte o arquivo [DOCUMENTACAO.md](DOCUMENTACAO.md) para:
- Detalhes da arquitetura
- Modelagem do banco de dados
- Guia de testes
- Exemplos de uso

