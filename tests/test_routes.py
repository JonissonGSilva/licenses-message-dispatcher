"""Testes para rotas da API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Database
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def test_db_setup():
    """Configura banco de dados de teste."""
    test_db_name = f"{settings.mongodb_db_name}_test"
    test_client = AsyncIOMotorClient(settings.mongodb_url)
    test_db = test_client[test_db_name]
    
    # Mock do Database.get_database
    original_get_db = Database.get_database
    
    def get_test_db():
        return test_db
    
    Database.get_database = get_test_db
    
    yield test_db
    
    # Limpa e restaura
    test_client.drop_database(test_db_name)
    test_client.close()
    Database.get_database = original_get_db


def test_root_endpoint():
    """Testa endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    assert "mensagem" in response.json()


def test_health_check():
    """Testa health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_criar_cliente(test_db_setup):
    """Testa criação de cliente via API."""
    cliente_data = {
        "nome": "João Silva",
        "email": "joao@example.com",
        "telefone": "5511999999999",
        "tipo_licenca": "Hub",
        "empresa": "Empresa XYZ"
    }
    
    response = client.post("/api/clientes", json=cliente_data)
    assert response.status_code == 201
    assert response.json()["nome"] == "João Silva"


def test_listar_clientes(test_db_setup):
    """Testa listagem de clientes."""
    response = client.get("/api/clientes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

