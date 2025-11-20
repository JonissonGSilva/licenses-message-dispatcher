"""Configuração de testes."""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.database import Database


@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes assíncronos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Configura banco de dados de teste."""
    # Usa um banco de dados separado para testes
    test_db_name = f"{settings.mongodb_db_name}_test"
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[test_db_name]
    
    yield db
    
    # Limpa o banco de teste após os testes
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
async def clean_db(test_db):
    """Limpa as coleções antes de cada teste."""
    collections = ["clientes", "licencas", "mensagens"]
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    yield test_db

