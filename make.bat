@echo off
REM Makefile alternativo para Windows
REM Uso: make.bat [comando]

set PYTHON=py
set PIP=py -m pip
set VENV=venv
set VENV_ACTIVATE=%VENV%\Scripts\activate.bat
set PYTEST=pytest
set UVICORN=uvicorn

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="setup" goto setup
if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="test" goto test
if "%1"=="test-cov" goto test-cov
if "%1"=="clean" goto clean
if "%1"=="check-env" goto check-env
if "%1"=="verify-env" goto verify-env
if "%1"=="create-indexes" goto create-indexes
goto help

:help
echo.
echo Comandos disponíveis:
echo   setup      - Prepara o ambiente (cria venv e instala dependencias)
echo   install    - Instala as dependencias do projeto
echo   run        - Executa o projeto (FastAPI)
echo   test       - Executa os testes
echo   test-cov   - Executa os testes com cobertura
echo   clean      - Limpa arquivos temporarios
echo   check-env      - Verifica se o arquivo .env esta configurado
echo   verify-env     - Verifica configuracoes do .env (requer Python)
echo   create-indexes - Cria indices no MongoDB para melhorar performance
echo   help           - Mostra esta mensagem
echo.
goto end

:setup
echo Preparando ambiente...
if not exist "%VENV%" (
    echo Criando ambiente virtual...
    %PYTHON% -m venv %VENV%
)
echo Instalando dependencias...
call %VENV_ACTIVATE%
%PIP% install --upgrade pip
%PIP% install -r requirements.txt
if not exist .env (
    echo Criando arquivo .env a partir do .env.example...
    copy .env.example .env
    echo Arquivo .env criado. Configure as variaveis de ambiente!
)
echo Ambiente preparado com sucesso!
echo Ative o ambiente virtual com: %VENV_ACTIVATE%
goto end

:install
echo Instalando dependencias...
%PIP% install --upgrade pip
%PIP% install -r requirements.txt
echo Dependencias instaladas com sucesso!
goto end

:run
echo Iniciando aplicacao...
if not exist "%VENV%" (
    echo Ambiente virtual nao encontrado. Execute 'make.bat setup' primeiro.
    exit /b 1
)
call %VENV_ACTIVATE%
%UVICORN% app.main:app --reload --host 0.0.0.0 --port 8000
goto end

:test
echo Executando testes...
if not exist "%VENV%" (
    echo Ambiente virtual nao encontrado. Execute 'make.bat setup' primeiro.
    exit /b 1
)
call %VENV_ACTIVATE%
%PYTEST% -v
goto end

:test-cov
echo Executando testes com cobertura...
if not exist "%VENV%" (
    echo Ambiente virtual nao encontrado. Execute 'make.bat setup' primeiro.
    exit /b 1
)
call %VENV_ACTIVATE%
%PYTEST% --cov=app --cov-report=html --cov-report=term
echo Relatorio de cobertura gerado em htmlcov\index.html
goto end

:clean
echo Limpando arquivos temporarios...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
if exist .pytest_cache rd /s /q .pytest_cache 2>nul
if exist .coverage del /q .coverage 2>nul
if exist htmlcov rd /s /q htmlcov 2>nul
if exist dist rd /s /q dist 2>nul
if exist build rd /s /q build 2>nul
echo Limpeza concluida!
goto end

:check-env
if not exist .env (
    echo Arquivo .env nao encontrado!
    echo Execute: copy .env.example .env
    exit /b 1
) else (
    echo Arquivo .env encontrado.
    echo Verifique se todas as variaveis estao configuradas.
)
goto end

:verify-env
echo Verificando configuracoes do .env...
if not exist "%VENV%" (
    echo Ambiente virtual nao encontrado. Execute 'make.bat setup' primeiro.
    exit /b 1
)
call %VENV_ACTIVATE%
python scripts\check_env.py
goto end

:create-indexes
echo Criando indices no MongoDB...
if not exist "%VENV%" (
    echo Ambiente virtual nao encontrado. Execute 'make.bat setup' primeiro.
    exit /b 1
)
call %VENV_ACTIVATE%
python scripts\create_indexes.py
goto end

:end

