"""Testes para CSVService."""
import pytest
from io import BytesIO
import pandas as pd
from app.services.csv_service import CSVService
from app.models.cliente import ClienteCreate


def criar_csv_bytes(dados: list) -> BytesIO:
    """Cria um arquivo CSV em memória."""
    df = pd.DataFrame(dados)
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    return buffer


@pytest.mark.asyncio
async def test_processar_csv_valido():
    """Testa processamento de CSV válido."""
    dados = [
        {
            "nome": "João Silva",
            "email": "joao@example.com",
            "telefone": "11999999999",
            "tipo_licenca": "Hub",
            "empresa": "Empresa XYZ"
        },
        {
            "nome": "Maria Santos",
            "email": "maria@example.com",
            "telefone": "21888888888",
            "tipo_licenca": "Start",
            "empresa": "Empresa ABC"
        }
    ]
    
    arquivo = criar_csv_bytes(dados)
    resultado = await CSVService.processar_csv(arquivo)
    
    assert resultado["sucesso"] == 2
    assert len(resultado["clientes"]) == 2
    assert len(resultado["erros"]) == 0
    
    cliente1 = resultado["clientes"][0]
    assert cliente1.nome == "João Silva"
    assert cliente1.tipo_licenca == "Hub"
    assert cliente1.telefone.startswith("55")


@pytest.mark.asyncio
async def test_processar_csv_com_erros():
    """Testa processamento de CSV com erros."""
    dados = [
        {
            "nome": "João Silva",
            "telefone": "11999999999",
            "tipo_licenca": "Hub"
        },
        {
            "nome": "Maria Santos",
            "telefone": "123",  # Telefone inválido
            "tipo_licenca": "Start"
        },
        {
            "nome": "Pedro",
            "telefone": "21988888888",
            "tipo_licenca": "Invalid"  # Tipo inválido
        }
    ]
    
    arquivo = criar_csv_bytes(dados)
    resultado = await CSVService.processar_csv(arquivo)
    
    assert resultado["sucesso"] == 1
    assert len(resultado["erros"]) == 2


@pytest.mark.asyncio
async def test_processar_csv_vazio():
    """Testa processamento de CSV vazio."""
    dados = []
    arquivo = criar_csv_bytes(dados)
    
    with pytest.raises(ValueError, match="vazio"):
        await CSVService.processar_csv(arquivo)


@pytest.mark.asyncio
async def test_validar_telefone():
    """Testa validação de telefone."""
    # Telefone válido
    assert CSVService.validar_telefone("11999999999") == "5511999999999"
    assert CSVService.validar_telefone("5511999999999") == "5511999999999"
    
    # Telefone inválido
    assert CSVService.validar_telefone("123") is None
    assert CSVService.validar_telefone("") is None


@pytest.mark.asyncio
async def test_validar_tipo_licenca():
    """Testa validação de tipo de licença."""
    assert CSVService.validar_tipo_licenca("Start") == "Start"
    assert CSVService.validar_tipo_licenca("Hub") == "Hub"
    assert CSVService.validar_tipo_licenca("start") == "Start"
    assert CSVService.validar_tipo_licenca("S") == "Start"
    assert CSVService.validar_tipo_licenca("Invalid") is None

