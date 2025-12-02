"""Script para criar índices no MongoDB para melhorar performance de queries."""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import Database
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_indexes():
    """Cria índices necessários no MongoDB."""
    try:
        logger.info("Conectando ao MongoDB...")
        await Database.connect()
        db = Database.get_database()
        
        logger.info("Criando índices...")
        
        # Índices para collection 'customers'
        customers_collection = db["customers"]
        
        # Índice para company.id (ObjectId) - permite queries rápidas por empresa
        logger.info("Criando índice em customers.company.id...")
        await customers_collection.create_index("company.id", name="company_id_idx")
        
        # Índice para phone (já usado para buscar duplicatas)
        logger.info("Criando índice em customers.phone...")
        await customers_collection.create_index("phone", name="phone_idx", unique=False)
        
        # Índice para email (já usado para buscar duplicatas)
        logger.info("Criando índice em customers.email...")
        await customers_collection.create_index("email", name="email_idx", unique=False, sparse=True)
        
        # Índice composto para license_type e active (usado em listagens)
        logger.info("Criando índice composto em customers.license_type e active...")
        await customers_collection.create_index(
            [("license_type", 1), ("active", 1)],
            name="license_type_active_idx"
        )
        
        # Índices para collection 'companies'
        companies_collection = db["companies"]
        
        # Índice único para CNPJ (se houver)
        logger.info("Criando índice em companies.cnpj...")
        await companies_collection.create_index("cnpj", name="cnpj_idx", unique=False, sparse=True)
        
        # Índice para name (usado para buscar empresas)
        logger.info("Criando índice em companies.name...")
        await companies_collection.create_index("name", name="name_idx", unique=False)
        
        # Índice para portal_id (se houver)
        logger.info("Criando índice em companies.portal_id...")
        await companies_collection.create_index("portal_id", name="portal_id_idx", unique=False, sparse=True)
        
        # Índice composto para active e linked
        logger.info("Criando índice composto em companies.active e linked...")
        await companies_collection.create_index(
            [("active", 1), ("linked", 1)],
            name="active_linked_idx"
        )
        
        logger.info("✅ Todos os índices foram criados com sucesso!")
        
        # Lista os índices criados
        logger.info("\n📊 Índices criados na collection 'customers':")
        customers_indexes = await customers_collection.list_indexes().to_list(length=None)
        for idx in customers_indexes:
            logger.info(f"  - {idx.get('name', 'N/A')}: {idx.get('key', {})}")
        
        logger.info("\n📊 Índices criados na collection 'companies':")
        companies_indexes = await companies_collection.list_indexes().to_list(length=None)
        for idx in companies_indexes:
            logger.info(f"  - {idx.get('name', 'N/A')}: {idx.get('key', {})}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar índices: {type(e).__name__}: {e}")
        logger.error(f"Detalhes:", exc_info=True)
        sys.exit(1)
    finally:
        await Database.disconnect()
        logger.info("Desconectado do MongoDB")


if __name__ == "__main__":
    asyncio.run(create_indexes())



