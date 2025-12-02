.PHONY: help install setup run test test-cov clean lint format docker-up docker-down create-indexes

# Variáveis
PYTHON := python
PIP := pip
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_ACTIVATE := $(VENV_BIN)/activate
PYTEST := pytest
UVICORN := uvicorn

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)Comandos disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instala as dependências do projeto
	@echo "$(GREEN)Instalando dependências...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependências instaladas com sucesso!$(NC)"

setup: ## Prepara o ambiente (cria venv e instala dependências)
	@echo "$(GREEN)Preparando ambiente...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Criando ambiente virtual...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "$(YELLOW)Instalando dependências...$(NC)"
	@. $(VENV_ACTIVATE) && $(PIP) install --upgrade pip
	@. $(VENV_ACTIVATE) && $(PIP) install -r requirements.txt
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Criando arquivo .env a partir do .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)Arquivo .env criado. Configure as variáveis de ambiente!$(NC)"; \
	fi
	@echo "$(GREEN)Ambiente preparado com sucesso!$(NC)"
	@echo "$(YELLOW)Ative o ambiente virtual com: source $(VENV_ACTIVATE)$(NC)"

run: ## Executa o projeto (FastAPI)
	@echo "$(GREEN)Iniciando aplicação...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Executa o projeto em modo produção
	@echo "$(GREEN)Iniciando aplicação em modo produção...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Executa os testes
	@echo "$(GREEN)Executando testes...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && $(PYTEST) -v

test-cov: ## Executa os testes com cobertura
	@echo "$(GREEN)Executando testes com cobertura...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && $(PYTEST) --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)Relatório de cobertura gerado em htmlcov/index.html$(NC)"

test-watch: ## Executa os testes em modo watch (requer pytest-watch)
	@echo "$(GREEN)Executando testes em modo watch...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && ptw -- -v

lint: ## Executa linter (flake8, se disponível)
	@echo "$(GREEN)Executando linter...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics || echo "$(YELLOW)Flake8 não instalado. Instale com: pip install flake8$(NC)"

format: ## Formata o código (black, se disponível)
	@echo "$(GREEN)Formatando código...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && black app tests --check || echo "$(YELLOW)Black não instalado. Instale com: pip install black$(NC)"

clean: ## Limpa arquivos temporários e cache
	@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	rm -rf dist 2>/dev/null || true
	rm -rf build 2>/dev/null || true
	@echo "$(GREEN)Limpeza concluída!$(NC)"

clean-all: clean ## Limpa tudo incluindo ambiente virtual
	@echo "$(GREEN)Limpando ambiente virtual...$(NC)"
	rm -rf $(VENV) 2>/dev/null || true
	@echo "$(GREEN)Limpeza completa!$(NC)"

docker-up: ## Inicia MongoDB via Docker (se docker-compose.yml existir)
	@if [ -f docker-compose.yml ]; then \
		echo "$(GREEN)Iniciando MongoDB via Docker...$(NC)"; \
		docker-compose up -d; \
	else \
		echo "$(YELLOW)docker-compose.yml não encontrado.$(NC)"; \
	fi

docker-down: ## Para MongoDB via Docker
	@if [ -f docker-compose.yml ]; then \
		echo "$(GREEN)Parando MongoDB via Docker...$(NC)"; \
		docker-compose down; \
	else \
		echo "$(YELLOW)docker-compose.yml não encontrado.$(NC)"; \
	fi

check-env: ## Verifica se o arquivo .env está configurado
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Arquivo .env não encontrado!$(NC)"; \
		echo "$(YELLOW)Execute: cp .env.example .env$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)Arquivo .env encontrado.$(NC)"; \
		echo "$(YELLOW)Verifique se todas as variáveis estão configuradas.$(NC)"; \
	fi

verify-env: ## Verifica configurações do .env (requer Python)
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && python scripts/check_env.py

create-indexes: ## Cria índices no MongoDB para melhorar performance
	@echo "$(GREEN)Criando índices no MongoDB...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && python scripts/create_indexes.py

seed: ## Popula o banco de dados com dados de exemplo (seed)
	@echo "$(GREEN)Populando banco de dados com dados de exemplo...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Ambiente virtual não encontrado. Execute 'make setup' primeiro.$(NC)"; \
		exit 1; \
	fi
	@. $(VENV_ACTIVATE) && python scripts/seed_database.py

dev: setup check-env run ## Setup completo + executa o projeto (atalho)

.DEFAULT_GOAL := help

