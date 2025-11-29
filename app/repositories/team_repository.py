"""Repository for Team operations (Direta, Indicador, Parceiro, Negocio)."""
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.team import (
    Direta, DiretaCreate, DiretaUpdate,
    Indicador, IndicadorCreate, IndicadorUpdate,
    Parceiro, ParceiroCreate, ParceiroUpdate,
    Negocio, NegocioCreate, NegocioUpdate
)
from app.repositories.company_repository import CompanyRepository
from app.models.customer import normalize_company_field
import logging

logger = logging.getLogger(__name__)


class TeamRepository:
    """Base repository methods for team collections."""
    
    @staticmethod
    async def resolve_company_reference(company_name: Optional[str], validate_status: bool = True) -> Optional[Dict[str, Any]]:
        """
        Resolves a company name to a company reference (id and name).
        
        Args:
            company_name: Company name to search for
            validate_status: If True, validates that company is linked=True and active=True
            
        Returns:
            Dict with 'id' (ObjectId) and 'name' if company found and valid, None otherwise
        """
        if not company_name or not company_name.strip():
            return None
        
        try:
            company = await CompanyRepository.find_by_name(company_name.strip())
            if company:
                # Validate status if required
                if validate_status:
                    if not company.linked or not company.active:
                        logger.warning(
                            f"Company '{company.name}' (ID: {company.id}) is not valid: "
                            f"linked={company.linked}, active={company.active}"
                        )
                        return None
                
                logger.debug(f"Company found and valid: {company.name} (ID: {company.id})")
                return {
                    "id": company.id,  # ObjectId, not string
                    "name": company.name
                }
            else:
                logger.debug(f"Company not found: {company_name}")
                return None
        except Exception as e:
            logger.warning(f"Error resolving company reference for '{company_name}': {type(e).__name__}: {e}")
            return None


class DiretaRepository:
    """Repository for managing Direta team members."""
    
    @staticmethod
    def get_collection():
        """Returns the direta collection."""
        return Database.get_database()["direta"]
    
    @staticmethod
    async def create(direta: DiretaCreate) -> Direta:
        """Creates a new Direta member."""
        collection = DiretaRepository.get_collection()
        
        try:
            direta_dict = direta.model_dump()
            direta_dict["created_at"] = datetime.utcnow()
            direta_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating direta member: {direta.nome}")
            result = await collection.insert_one(direta_dict)
            direta_dict["_id"] = result.inserted_id
            
            direta_created = Direta(**direta_dict)
            logger.info(f"Direta member created: ID={result.inserted_id}, Name={direta.nome}")
            return direta_created
        except Exception as e:
            logger.error(f"Error creating direta member: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def get_by_id(direta_id: str) -> Optional[Direta]:
        """Gets a Direta member by ID."""
        collection = DiretaRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(direta_id):
                return None
            
            doc = await collection.find_one({"_id": ObjectId(direta_id)})
            if doc:
                return Direta(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting direta member: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Direta]:
        """Lists all Direta members with pagination."""
        collection = DiretaRepository.get_collection()
        
        try:
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            return [Direta(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listing direta members: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def count() -> int:
        """Counts total Direta members."""
        collection = DiretaRepository.get_collection()
        return await collection.count_documents({})
    
    @staticmethod
    async def update(direta_id: str, direta_update: DiretaUpdate) -> Optional[Direta]:
        """Updates a Direta member."""
        collection = DiretaRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(direta_id):
                return None
            
            update_dict = direta_update.model_dump(exclude_unset=True)
            if not update_dict:
                return await DiretaRepository.get_by_id(direta_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(direta_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                return Direta(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating direta member: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def delete(direta_id: str) -> bool:
        """Deletes a Direta member."""
        collection = DiretaRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(direta_id):
                return False
            
            result = await collection.delete_one({"_id": ObjectId(direta_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting direta member: {type(e).__name__}: {e}")
            raise


class IndicadorRepository:
    """Repository for managing Indicador team members."""
    
    @staticmethod
    def get_collection():
        """Returns the indicador collection."""
        return Database.get_database()["indicador"]
    
    @staticmethod
    async def create(indicador: IndicadorCreate) -> Indicador:
        """Creates a new Indicador."""
        collection = IndicadorRepository.get_collection()
        
        try:
            indicador_dict = indicador.model_dump()
            
            # Resolve company reference if company name is provided
            if indicador.empresa and isinstance(indicador.empresa, str):
                company_ref = await TeamRepository.resolve_company_reference(indicador.empresa, validate_status=True)
                if company_ref:
                    indicador_dict["empresa"] = company_ref
                    logger.debug(f"Company reference resolved: {company_ref['name']} (ID: {company_ref['id']})")
                else:
                    logger.warning(f"Company '{indicador.empresa}' not found, is not linked, or is not active")
                    raise ValueError(f"Company '{indicador.empresa}' not found, is not linked, or is not active")
            
            indicador_dict["created_at"] = datetime.utcnow()
            indicador_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating indicador: {indicador.nome}")
            result = await collection.insert_one(indicador_dict)
            indicador_dict["_id"] = result.inserted_id
            
            indicador_created = Indicador(**indicador_dict)
            logger.info(f"Indicador created: ID={result.inserted_id}, Name={indicador.nome}")
            return indicador_created
        except Exception as e:
            logger.error(f"Error creating indicador: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def get_by_id(indicador_id: str) -> Optional[Indicador]:
        """Gets an Indicador by ID."""
        collection = IndicadorRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(indicador_id):
                return None
            
            doc = await collection.find_one({"_id": ObjectId(indicador_id)})
            if doc:
                return Indicador(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting indicador: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Indicador]:
        """Lists all Indicadores with pagination."""
        collection = IndicadorRepository.get_collection()
        
        try:
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            return [Indicador(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listing indicadores: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def count() -> int:
        """Counts total Indicadores."""
        collection = IndicadorRepository.get_collection()
        return await collection.count_documents({})
    
    @staticmethod
    async def update(indicador_id: str, indicador_update: IndicadorUpdate) -> Optional[Indicador]:
        """Updates an Indicador."""
        collection = IndicadorRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(indicador_id):
                return None
            
            update_dict = indicador_update.model_dump(exclude_unset=True)
            
            # Resolve company reference if company name is provided
            if "empresa" in update_dict and isinstance(update_dict["empresa"], str):
                company_ref = await TeamRepository.resolve_company_reference(update_dict["empresa"], validate_status=True)
                if company_ref:
                    update_dict["empresa"] = company_ref
                else:
                    raise ValueError(f"Company '{update_dict['empresa']}' not found, is not linked, or is not active")
            
            if not update_dict:
                return await IndicadorRepository.get_by_id(indicador_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(indicador_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                return Indicador(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating indicador: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def delete(indicador_id: str) -> bool:
        """Deletes an Indicador."""
        collection = IndicadorRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(indicador_id):
                return False
            
            result = await collection.delete_one({"_id": ObjectId(indicador_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting indicador: {type(e).__name__}: {e}")
            raise


class ParceiroRepository:
    """Repository for managing Parceiro team members."""
    
    @staticmethod
    def get_collection():
        """Returns the parceiro collection."""
        return Database.get_database()["parceiro"]
    
    @staticmethod
    async def create(parceiro: ParceiroCreate) -> Parceiro:
        """Creates a new Parceiro."""
        collection = ParceiroRepository.get_collection()
        
        try:
            parceiro_dict = parceiro.model_dump()
            
            # Resolve company reference if company name is provided
            if parceiro.empresa and isinstance(parceiro.empresa, str):
                company_ref = await TeamRepository.resolve_company_reference(parceiro.empresa, validate_status=True)
                if company_ref:
                    parceiro_dict["empresa"] = company_ref
                    logger.debug(f"Company reference resolved: {company_ref['name']} (ID: {company_ref['id']})")
                else:
                    logger.warning(f"Company '{parceiro.empresa}' not found, is not linked, or is not active")
                    raise ValueError(f"Company '{parceiro.empresa}' not found, is not linked, or is not active")
            
            parceiro_dict["created_at"] = datetime.utcnow()
            parceiro_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating parceiro: {parceiro.nome}")
            result = await collection.insert_one(parceiro_dict)
            parceiro_dict["_id"] = result.inserted_id
            
            parceiro_created = Parceiro(**parceiro_dict)
            logger.info(f"Parceiro created: ID={result.inserted_id}, Name={parceiro.nome}")
            return parceiro_created
        except Exception as e:
            logger.error(f"Error creating parceiro: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def get_by_id(parceiro_id: str) -> Optional[Parceiro]:
        """Gets a Parceiro by ID."""
        collection = ParceiroRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return None
            
            doc = await collection.find_one({"_id": ObjectId(parceiro_id)})
            if doc:
                return Parceiro(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting parceiro: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Parceiro]:
        """Lists all Parceiros with pagination."""
        collection = ParceiroRepository.get_collection()
        
        try:
            cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
            docs = await cursor.to_list(length=limit)
            return [Parceiro(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listing parceiros: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def count() -> int:
        """Counts total Parceiros."""
        collection = ParceiroRepository.get_collection()
        return await collection.count_documents({})
    
    @staticmethod
    async def update(parceiro_id: str, parceiro_update: ParceiroUpdate) -> Optional[Parceiro]:
        """Updates a Parceiro."""
        collection = ParceiroRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return None
            
            update_dict = parceiro_update.model_dump(exclude_unset=True)
            
            # Resolve company reference if company name is provided
            if "empresa" in update_dict and isinstance(update_dict["empresa"], str):
                company_ref = await TeamRepository.resolve_company_reference(update_dict["empresa"], validate_status=True)
                if company_ref:
                    update_dict["empresa"] = company_ref
                else:
                    raise ValueError(f"Company '{update_dict['empresa']}' not found, is not linked, or is not active")
            
            if not update_dict:
                return await ParceiroRepository.get_by_id(parceiro_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(parceiro_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                return Parceiro(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating parceiro: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def delete(parceiro_id: str) -> bool:
        """Deletes a Parceiro."""
        collection = ParceiroRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return False
            
            result = await collection.delete_one({"_id": ObjectId(parceiro_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting parceiro: {type(e).__name__}: {e}")
            raise


class NegocioRepository:
    """Repository for managing Negocio (business deals)."""
    
    @staticmethod
    def get_collection():
        """Returns the negocio collection."""
        return Database.get_database()["negocio"]
    
    @staticmethod
    async def create(negocio: NegocioCreate, parceiro_id: str) -> Negocio:
        """Creates a new Negocio linked to a Parceiro."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                raise ValueError("Invalid parceiro_id")
            
            negocio_dict = negocio.model_dump()
            negocio_dict["parceiro_id"] = ObjectId(parceiro_id)
            negocio_dict["created_at"] = datetime.utcnow()
            negocio_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating negocio for parceiro: {parceiro_id}")
            result = await collection.insert_one(negocio_dict)
            negocio_dict["_id"] = result.inserted_id
            
            negocio_created = Negocio(**negocio_dict)
            logger.info(f"Negocio created: ID={result.inserted_id}")
            return negocio_created
        except Exception as e:
            logger.error(f"Error creating negocio: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def get_by_id(negocio_id: str) -> Optional[Negocio]:
        """Gets a Negocio by ID."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(negocio_id):
                return None
            
            doc = await collection.find_one({"_id": ObjectId(negocio_id)})
            if doc:
                return Negocio(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting negocio: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def list_by_parceiro(parceiro_id: str) -> List[Negocio]:
        """Lists all Negocios for a specific Parceiro."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return []
            
            cursor = collection.find({"parceiro_id": ObjectId(parceiro_id)}).sort("created_at", -1)
            docs = await cursor.to_list(length=None)
            return [Negocio(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listing negocios: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def update(negocio_id: str, negocio_update: NegocioUpdate) -> Optional[Negocio]:
        """Updates a Negocio."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(negocio_id):
                return None
            
            update_dict = negocio_update.model_dump(exclude_unset=True)
            if not update_dict:
                return await NegocioRepository.get_by_id(negocio_id)
            
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(negocio_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                return Negocio(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating negocio: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def delete(negocio_id: str) -> bool:
        """Deletes a Negocio."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(negocio_id):
                return False
            
            result = await collection.delete_one({"_id": ObjectId(negocio_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting negocio: {type(e).__name__}: {e}")
            raise

