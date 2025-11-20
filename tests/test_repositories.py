"""Testes para repositórios."""
import pytest
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.licenca_repository import LicencaRepository
from app.repositories.mensagem_repository import MensagemRepository
from app.models.cliente import ClienteCreate
from app.models.licenca import LicencaCreate
from app.models.mensagem import MensagemCreate
from bson import ObjectId


@pytest.mark.asyncio
async def test_cliente_repository_criar(clean_db):
    """Testa criação de cliente."""
    # Mock do Database.get_database para retornar o banco de teste
    original_get_db = ClienteRepository.get_collection
    ClienteRepository.get_collection = lambda: clean_db["clientes"]
    
    cliente = ClienteCreate(
        nome="João Silva",
        email="joao@example.com",
        telefone="5511999999999",
        tipo_licenca="Hub",
        empresa="Empresa XYZ"
    )
    
    cliente_criado = await ClienteRepository.criar(cliente)
    
    assert cliente_criado.id is not None
    assert cliente_criado.nome == "João Silva"
    assert cliente_criado.tipo_licenca == "Hub"
    
    # Restaura método original
    ClienteRepository.get_collection = original_get_db


@pytest.mark.asyncio
async def test_cliente_repository_buscar_por_telefone(clean_db):
    """Testa busca de cliente por telefone."""
    original_get_db = ClienteRepository.get_collection
    ClienteRepository.get_collection = lambda: clean_db["clientes"]
    
    cliente = ClienteCreate(
        nome="João Silva",
        telefone="5511999999999",
        tipo_licenca="Hub"
    )
    
    cliente_criado = await ClienteRepository.criar(cliente)
    cliente_buscado = await ClienteRepository.buscar_por_telefone("5511999999999")
    
    assert cliente_buscado is not None
    assert cliente_buscado.id == cliente_criado.id
    
    ClienteRepository.get_collection = original_get_db


@pytest.mark.asyncio
async def test_licenca_repository_criar(clean_db):
    """Testa criação de licença."""
    original_get_db_licenca = LicencaRepository.get_collection
    original_get_db_cliente = ClienteRepository.get_collection
    
    LicencaRepository.get_collection = lambda: clean_db["licencas"]
    ClienteRepository.get_collection = lambda: clean_db["clientes"]
    
    # Cria cliente primeiro
    cliente = ClienteCreate(
        nome="João Silva",
        telefone="5511999999999",
        tipo_licenca="Hub"
    )
    cliente_criado = await ClienteRepository.criar(cliente)
    
    # Cria licença
    licenca = LicencaCreate(
        cliente_id=cliente_criado.id,
        tipo_licenca="Hub",
        status="ativa",
        portal_id="LIC-123"
    )
    
    licenca_criada = await LicencaRepository.criar(licenca)
    
    assert licenca_criada.id is not None
    assert licenca_criada.portal_id == "LIC-123"
    
    LicencaRepository.get_collection = original_get_db_licenca
    ClienteRepository.get_collection = original_get_db_cliente

