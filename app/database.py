"""Configuração e conexão com MongoDB."""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Classe para gerenciar conexão com MongoDB."""
    
    client: AsyncIOMotorClient = None
    database = None
    
    @classmethod
    async def connect(cls):
        """Conecta ao MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.database = cls.client[settings.mongodb_db_name]
            
            # Testa a conexão
            await cls.client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida com sucesso")
            
        except ConnectionFailure as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Desconecta do MongoDB."""
        if cls.client:
            cls.client.close()
            logger.info("Desconectado do MongoDB")
    
    @classmethod
    def get_database(cls):
        """Retorna a instância do banco de dados."""
        return cls.database

