"""Repository for Team operations (Direta, Indicador, Parceiro, Negocio)."""
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
from app.database import Database
from app.models.team import (
    Direta, DiretaCreate, DiretaUpdate,
    Indicador, IndicadorCreate, IndicadorUpdate,
    Parceiro, ParceiroCreate, ParceiroUpdate,
    Negocio, NegocioCreate, NegocioUpdate
)
from app.repositories.company_repository import CompanyRepository
from app.models.customer import normalize_company_field, normalize_company_array_field
import logging

logger = logging.getLogger(__name__)


class TeamRepository:
    """Base repository methods for team collections."""
    
    @staticmethod
    async def resolve_company_reference(company_name: Optional[str], validate_status: bool = True) -> Optional[Dict[str, Any]]:
        """
        Resolves a company name to a company reference (id, name, and isCompanyActive).
        
        Args:
            company_name: Company name to search for
            validate_status: If True, validates that company is active=True
            
        Returns:
            Dict with 'id' (ObjectId), 'name', and 'isCompanyActive' if company found and valid, None otherwise
        """
        if not company_name or not company_name.strip():
            return None
        
        try:
            company = await CompanyRepository.find_by_name(company_name.strip())
            if company:
                # Validate status if required
                if validate_status:
                    if not company.active:
                        logger.warning(
                            f"Company '{company.name}' (ID: {company.id}) is not valid: "
                            f"active={company.active}"
                        )
                        return None
                
                logger.debug(f"Company found and valid: {company.name} (ID: {company.id})")
                # Determine if company is active based on status and active field
                # Company is active if status is "ativo" and active is True
                is_company_active = (
                    company.status == "ativo" and 
                    company.active is True
                )
                return {
                    "id": company.id,  # ObjectId, not string
                    "name": company.name,
                    "isCompanyActive": is_company_active,
                    "license_type": company.license_type if hasattr(company, "license_type") else None
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
        return Database.get_database()["direct"]
    
    @staticmethod
    async def create(direta: DiretaCreate) -> Direta:
        """Creates a new Direta member."""
        collection = DiretaRepository.get_collection()
        
        try:
            direta_dict = direta.model_dump()
            direta_dict["created_at"] = datetime.now(timezone.utc)
            direta_dict["updated_at"] = datetime.now(timezone.utc)
            
            logger.debug(f"Creating direta member: {direta.name}")
            result = await collection.insert_one(direta_dict)
            direta_dict["_id"] = result.inserted_id
            
            direta_created = Direta(**direta_dict)
            logger.info(f"Direta member created: ID={result.inserted_id}, Name={direta.name}")
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
            
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
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
        return Database.get_database()["indicator"]
    
    @staticmethod
    async def create(indicador: IndicadorCreate) -> Indicador:
        """Creates a new Indicador."""
        collection = IndicadorRepository.get_collection()
        
        try:
            indicador_dict = indicador.model_dump()
            
            # Normalize company field - handle both old (single) and new (array) formats
            # Only one company can be active at a time
            companies_list = []
            if indicador.company:
                # If it's a list, process each item (only first one will be active)
                if isinstance(indicador.company, list):
                    for idx, company_item in enumerate(indicador.company):
                        if isinstance(company_item, str):
                            company_ref = await TeamRepository.resolve_company_reference(company_item, validate_status=True)
                            if company_ref:
                                # Only first company is active
                                company_ref["isCompanyActive"] = (idx == 0)
                                companies_list.append(company_ref)
                            else:
                                raise ValueError(f"Company '{company_item}' not found or is not active")
                        elif isinstance(company_item, dict):
                            # Only first company is active
                            company_item = company_item.copy()
                            company_item["isCompanyActive"] = (idx == 0)
                            companies_list.append(company_item)
                # Backward compatibility: if it's a string, convert to list
                elif isinstance(indicador.company, str):
                    company_ref = await TeamRepository.resolve_company_reference(indicador.company, validate_status=True)
                    if company_ref:
                        company_ref["isCompanyActive"] = True  # First and only company is active
                        companies_list.append(company_ref)
                    else:
                        raise ValueError(f"Company '{indicador.company}' not found or is not active")
                elif isinstance(indicador.company, dict):
                    company_dict = indicador.company.copy()
                    company_dict["isCompanyActive"] = True  # First and only company is active
                    companies_list.append(company_dict)
            
            indicador_dict["company"] = companies_list
            indicador_dict["created_at"] = datetime.now(timezone.utc)
            indicador_dict["updated_at"] = datetime.now(timezone.utc)
            
            logger.debug(f"Creating indicador: {indicador.name}")
            result = await collection.insert_one(indicador_dict)
            indicador_dict["_id"] = result.inserted_id
            
            indicador_created = Indicador(**indicador_dict)
            logger.info(f"Indicador created: ID={result.inserted_id}, Name={indicador.name}")
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
                # Normalize company field for backward compatibility
                if "company" in doc and doc["company"] is not None:
                    doc["company"] = normalize_company_array_field(doc["company"])
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
            # Normalize company field for backward compatibility
            normalized_docs = []
            for doc in docs:
                if "company" in doc and doc["company"] is not None:
                    doc["company"] = normalize_company_array_field(doc["company"])
                normalized_docs.append(Indicador(**doc))
            return normalized_docs
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
            
            # Normalize company field if provided
            # Only one company can be active at a time
            if "company" in update_dict and update_dict["company"] is not None:
                companies_list = []
                if isinstance(update_dict["company"], list):
                    for idx, company_item in enumerate(update_dict["company"]):
                        if isinstance(company_item, str):
                            company_ref = await TeamRepository.resolve_company_reference(company_item, validate_status=True)
                            if company_ref:
                                # Only first company is active
                                company_ref["isCompanyActive"] = (idx == 0)
                                companies_list.append(company_ref)
                            else:
                                raise ValueError(f"Company '{company_item}' not found or is not active")
                        elif isinstance(company_item, dict):
                            # Only first company is active
                            company_item = company_item.copy()
                            company_item["isCompanyActive"] = (idx == 0)
                            companies_list.append(company_item)
                elif isinstance(update_dict["company"], str):
                    company_ref = await TeamRepository.resolve_company_reference(update_dict["company"], validate_status=True)
                    if company_ref:
                        company_ref["isCompanyActive"] = True  # First and only company is active
                        companies_list.append(company_ref)
                    else:
                        raise ValueError(f"Company '{update_dict['company']}' not found or is not active")
                elif isinstance(update_dict["company"], dict):
                    company_dict = update_dict["company"].copy()
                    company_dict["isCompanyActive"] = True  # First and only company is active
                    companies_list.append(company_dict)
                
                update_dict["company"] = companies_list
            
            if not update_dict:
                return await IndicadorRepository.get_by_id(indicador_id)
            
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(indicador_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Indicador(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating indicador: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def update_company_active_status(company_id: ObjectId, is_company_active: bool) -> int:
        """
        Updates the isCompanyActive field for all indicadores that belong to this company.
        Handles both old format (single object) and new format (array).
        
        Args:
            company_id: Company ObjectId
            is_company_active: New active status for the company
            
        Returns:
            Number of indicadores updated
        """
        collection = IndicadorRepository.get_collection()
        
        try:
            # Find all indicadores that have this company (both formats)
            indicadores_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            indicadores_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate
            all_indicadores = {}
            for indicador in indicadores_array:
                all_indicadores[str(indicador["_id"])] = indicador
            for indicador in indicadores_single:
                all_indicadores[str(indicador["_id"])] = indicador
            
            updated_count = 0
            for indicador_doc in all_indicadores.values():
                updated = False
                
                if "company" in indicador_doc:
                    # Handle array format
                    if isinstance(indicador_doc["company"], list):
                        # Count how many companies exist
                        has_multiple_companies = len(indicador_doc["company"]) > 1
                        
                        for company in indicador_doc["company"]:
                            if isinstance(company, dict):
                                company_id_in_doc = company.get("id")
                                if company_id_in_doc:
                                    company_matches = False
                                    if isinstance(company_id_in_doc, ObjectId):
                                        company_matches = (company_id_in_doc == company_id)
                                    elif str(company_id_in_doc) == str(company_id):
                                        company_matches = True
                                    
                                    if company_matches:
                                        # If indicador has only one company (or this is the only active one), always update
                                        # If indicador has multiple companies, only update the active one (preserve historical)
                                        current_is_active = company.get("isCompanyActive", True)
                                        if not has_multiple_companies or current_is_active:
                                            company["isCompanyActive"] = is_company_active
                                            updated = True
                    
                    # Handle single object format
                    # Always update single object format (it's the only company)
                    elif isinstance(indicador_doc["company"], dict):
                        company_id_in_doc = indicador_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Single object format - always update (it's the only company)
                                indicador_doc["company"]["isCompanyActive"] = is_company_active
                                updated = True
                
                if updated:
                    await collection.update_one(
                        {"_id": indicador_doc["_id"]},
                        {
                            "$set": {
                                "company": indicador_doc["company"],
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated isCompanyActive to {is_company_active} for {updated_count} indicador(es) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating company active status in indicadores: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def update_license_type_by_company(company_id: ObjectId, new_license_type: str) -> int:
        """
        Updates the license type for all indicadores that belong to this company (active company only).
        Handles both old format (single object) and new format (array).
        Only updates indicadores with the company as active (isCompanyActive=True).
        
        Args:
            company_id: Company ObjectId
            new_license_type: New license type (Start or Hub)
            
        Returns:
            Number of indicadores updated
        """
        collection = IndicadorRepository.get_collection()
        
        try:
            # Find all indicadores that have this company (both formats: array and single object)
            # Query for array format
            indicadores_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            # Query for single object format (backward compatibility)
            indicadores_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate by _id
            all_indicadores = {}
            for indicador in indicadores_array:
                all_indicadores[str(indicador["_id"])] = indicador
            for indicador in indicadores_single:
                all_indicadores[str(indicador["_id"])] = indicador
            
            updated_count = 0
            for indicador_doc in all_indicadores.values():
                should_update = False
                
                if "company" in indicador_doc:
                    # Handle array format
                    if isinstance(indicador_doc["company"], list):
                        for company in indicador_doc["company"]:
                            if isinstance(company, dict):
                                company_id_in_doc = company.get("id")
                                if company_id_in_doc:
                                    company_matches = False
                                    if isinstance(company_id_in_doc, ObjectId):
                                        company_matches = (company_id_in_doc == company_id)
                                    elif str(company_id_in_doc) == str(company_id):
                                        company_matches = True
                                    
                                    if company_matches:
                                        # Only update if the company is currently active
                                        # Don't update historical companies (isCompanyActive: false)
                                        current_is_active = company.get("isCompanyActive", True)
                                        if current_is_active:
                                            should_update = True
                                            break
                    
                    # Handle single object format (backward compatibility)
                    elif isinstance(indicador_doc["company"], dict):
                        company_id_in_doc = indicador_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Only update if the company is currently active
                                current_is_active = indicador_doc["company"].get("isCompanyActive", True)
                                if current_is_active:
                                    should_update = True
                
                if should_update:
                    await collection.update_one(
                        {"_id": indicador_doc["_id"]},
                        {
                            "$set": {
                                "license_type": new_license_type,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated license type to '{new_license_type}' for {updated_count} indicador(es) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating license type by company in indicadores: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def link_company(indicador_id: str, company_name: str) -> Optional[Indicador]:
        """
        Links a company to an Indicador. 
        - Validates that the company is not already linked (as active)
        - Marks previous active company as inactive (isCompanyActive=False)
        - Only one company can be active at a time
        - Reactivates an existing inactive company if found
        """
        collection = IndicadorRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(indicador_id):
                return None
            
            # Resolve company reference
            company_ref = await TeamRepository.resolve_company_reference(company_name, validate_status=True)
            if not company_ref:
                raise ValueError(f"Company '{company_name}' not found or is not active")
            
            # Get current indicador
            indicador = await IndicadorRepository.get_by_id(indicador_id)
            if not indicador:
                raise ValueError("Indicador não encontrado")
            
            # Normalize existing companies to list of dicts
            existing_companies = []
            if indicador.company:
                if isinstance(indicador.company, list):
                    for company_item in indicador.company:
                        if hasattr(company_item, "model_dump"):
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(indicador.company, dict):
                    if hasattr(indicador.company, "model_dump"):
                        existing_companies.append(indicador.company.model_dump())
                    else:
                        existing_companies.append(indicador.company.copy())
                elif isinstance(indicador.company, str):
                    existing_ref = await TeamRepository.resolve_company_reference(indicador.company, validate_status=False)
                    if existing_ref:
                        existing_companies.append(existing_ref)
            
            # Check if company is already linked (by ID)
            company_id = company_ref["id"]
            company_already_exists = False
            existing_company_index = -1
            
            for idx, existing_company in enumerate(existing_companies):
                if isinstance(existing_company, dict):
                    existing_id = existing_company.get("id")
                    if existing_id and str(existing_id) == str(company_id):
                        is_active = existing_company.get("isCompanyActive", True)
                        if is_active:
                            raise ValueError(f"Company '{company_name}' is already linked as active to this indicador")
                        # Company exists but is inactive - we'll reactivate it
                        company_already_exists = True
                        existing_company_index = idx
                        break
            
            if company_already_exists:
                # Company already exists in the array - reactivate it instead of duplicating
                # Mark all other companies as inactive
                for idx, existing_company in enumerate(existing_companies):
                    if isinstance(existing_company, dict):
                        if idx != existing_company_index:
                            existing_company["isCompanyActive"] = False
                        else:
                            # Reactivate the existing company entry
                            existing_company["isCompanyActive"] = True
                            # Update name in case it changed
                            existing_company["name"] = company_ref.get("name", existing_company.get("name"))
            else:
                # Company doesn't exist - add it as new
                # Mark all existing companies as inactive (historical)
                for existing_company in existing_companies:
                    if isinstance(existing_company, dict):
                        existing_company["isCompanyActive"] = False
                
                # Add new company as active
                company_ref["isCompanyActive"] = True
                existing_companies.append(company_ref)
            
            # Update indicador
            update_dict = {
                "company": existing_companies,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(indicador_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Indicador(**result)
            return None
        except Exception as e:
            logger.error(f"Error linking company to indicador: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def unlink_company(indicador_id: str) -> Optional[Indicador]:
        """
        Unlinks a company from an Indicador by removing it from the company array.
        Prioritizes removing the active company (isCompanyActive=True) if it exists.
        If no active company exists, removes the first company in the array.
        The company doesn't need to be active to be unlinked.
        
        Args:
            indicador_id: Indicador ID
            
        Returns:
            Updated Indicador or None if not found
        """
        collection = IndicadorRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(indicador_id):
                return None
            
            # Get current indicador
            indicador = await IndicadorRepository.get_by_id(indicador_id)
            if not indicador:
                raise ValueError("Indicador não encontrado")
            
            # Normalize existing companies to list of dicts
            existing_companies = []
            if indicador.company:
                if isinstance(indicador.company, list):
                    for company_item in indicador.company:
                        if hasattr(company_item, "model_dump"):
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(indicador.company, dict):
                    if hasattr(indicador.company, "model_dump"):
                        existing_companies.append(indicador.company.model_dump())
                    else:
                        existing_companies.append(indicador.company.copy())
                elif isinstance(indicador.company, str):
                    existing_ref = await TeamRepository.resolve_company_reference(indicador.company, validate_status=False)
                    if existing_ref:
                        existing_companies.append(existing_ref)
            
            if not existing_companies:
                raise ValueError("Nenhuma empresa vinculada para desvincular")
            
            # Find and remove company (prioritize active, but remove any if no active exists)
            company_removed = False
            updated_companies = []
            
            # First pass: remove active company if exists
            for company in existing_companies:
                if isinstance(company, dict):
                    is_active = company.get("isCompanyActive", True)
                    if is_active and not company_removed:
                        # Remove this active company
                        company_removed = True
                    else:
                        # Keep this company
                        updated_companies.append(company)
                else:
                    # Keep non-dict items (shouldn't happen, but just in case)
                    if not company_removed:
                        # Remove first non-dict item if no active company was found
                        company_removed = True
                    else:
                        updated_companies.append(company)
            
            # If no active company was found, remove the first company
            if not company_removed and existing_companies:
                # Remove first company
                updated_companies = existing_companies[1:]
                company_removed = True
            
            if not company_removed:
                raise ValueError("Nenhuma empresa encontrada para desvincular")
            
            # Update indicador
            update_dict = {
                "company": updated_companies,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(indicador_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Indicador(**result)
            return None
        except Exception as e:
            logger.error(f"Error unlinking company from indicador: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
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
        return Database.get_database()["partner"]
    
    @staticmethod
    async def create(parceiro: ParceiroCreate) -> Parceiro:
        """Creates a new Parceiro."""
        collection = ParceiroRepository.get_collection()
        
        try:
            parceiro_dict = parceiro.model_dump()
            
            # Normalize company field - handle both old (single) and new (array) formats
            companies_list = []
            if parceiro.company:
                # If it's a list, process each item
                if isinstance(parceiro.company, list):
                    for company_item in parceiro.company:
                        if isinstance(company_item, str):
                            company_ref = await TeamRepository.resolve_company_reference(company_item, validate_status=True)
                            if company_ref:
                                companies_list.append(company_ref)
                            else:
                                raise ValueError(f"Company '{company_item}' not found or is not active")
                        elif isinstance(company_item, dict):
                            companies_list.append(company_item)
                # Backward compatibility: if it's a string, convert to list
                elif isinstance(parceiro.company, str):
                    company_ref = await TeamRepository.resolve_company_reference(parceiro.company, validate_status=True)
                    if company_ref:
                        companies_list.append(company_ref)
                    else:
                        raise ValueError(f"Company '{parceiro.company}' not found or is not active")
                elif isinstance(parceiro.company, dict):
                    companies_list.append(parceiro.company)
            
            parceiro_dict["company"] = companies_list
            parceiro_dict["created_at"] = datetime.now(timezone.utc)
            parceiro_dict["updated_at"] = datetime.now(timezone.utc)
            
            logger.debug(f"Creating parceiro: {parceiro.name}")
            result = await collection.insert_one(parceiro_dict)
            parceiro_dict["_id"] = result.inserted_id
            
            parceiro_created = Parceiro(**parceiro_dict)
            logger.info(f"Parceiro created: ID={result.inserted_id}, Name={parceiro.name}")
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
                # Normalize company field for backward compatibility
                if "company" in doc and doc["company"] is not None:
                    doc["company"] = normalize_company_array_field(doc["company"])
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
            # Normalize company field for backward compatibility
            normalized_docs = []
            for doc in docs:
                if "company" in doc and doc["company"] is not None:
                    doc["company"] = normalize_company_array_field(doc["company"])
                normalized_docs.append(Parceiro(**doc))
            return normalized_docs
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
            
            # Normalize company field if provided
            if "company" in update_dict and update_dict["company"] is not None:
                companies_list = []
                if isinstance(update_dict["company"], list):
                    for company_item in update_dict["company"]:
                        if isinstance(company_item, str):
                            company_ref = await TeamRepository.resolve_company_reference(company_item, validate_status=True)
                            if company_ref:
                                companies_list.append(company_ref)
                            else:
                                raise ValueError(f"Company '{company_item}' not found or is not active")
                        elif isinstance(company_item, dict):
                            companies_list.append(company_item)
                elif isinstance(update_dict["company"], str):
                    company_ref = await TeamRepository.resolve_company_reference(update_dict["company"], validate_status=True)
                    if company_ref:
                        companies_list.append(company_ref)
                    else:
                        raise ValueError(f"Company '{update_dict['company']}' not found or is not active")
                elif isinstance(update_dict["company"], dict):
                    companies_list.append(update_dict["company"])
                
                update_dict["company"] = companies_list
            
            if not update_dict:
                return await ParceiroRepository.get_by_id(parceiro_id)
            
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(parceiro_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Parceiro(**result)
            return None
        except Exception as e:
            logger.error(f"Error updating parceiro: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def link_company(parceiro_id: str, company_name: str) -> Optional[Parceiro]:
        """Links a company to a Parceiro. Validates that the company is not already linked."""
        collection = ParceiroRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return None
            
            # Resolve company reference
            company_ref = await TeamRepository.resolve_company_reference(company_name, validate_status=True)
            if not company_ref:
                raise ValueError(f"Company '{company_name}' not found or is not active")
            
            # Get current parceiro
            parceiro = await ParceiroRepository.get_by_id(parceiro_id)
            if not parceiro:
                raise ValueError("Parceiro não encontrado")
            
            # Normalize existing companies to list
            # Convert to dicts to avoid Pydantic model serialization issues
            existing_companies = []
            if parceiro.company:
                if isinstance(parceiro.company, list):
                    for company_item in parceiro.company:
                        if hasattr(company_item, "model_dump"):
                            # Convert Pydantic model to dict
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(parceiro.company, dict):
                    if hasattr(parceiro.company, "model_dump"):
                        existing_companies.append(parceiro.company.model_dump())
                    else:
                        existing_companies.append(parceiro.company.copy())
                elif isinstance(parceiro.company, str):
                    # Try to resolve existing company
                    existing_ref = await TeamRepository.resolve_company_reference(parceiro.company, validate_status=False)
                    if existing_ref:
                        existing_companies.append(existing_ref)
            
            # Check if company is already linked (by ID) - avoid duplicates
            company_id = company_ref["id"]
            company_already_exists = False
            existing_company_index = None
            
            for idx, existing_company in enumerate(existing_companies):
                if isinstance(existing_company, dict):
                    existing_id = existing_company.get("id")
                    if existing_id and str(existing_id) == str(company_id):
                        is_active = existing_company.get("isCompanyActive", True)
                        if is_active:
                            raise ValueError(f"Company '{company_name}' is already linked as active to this parceiro")
                        # Company exists but is inactive - we'll reactivate it
                        company_already_exists = True
                        existing_company_index = idx
                        break
            
            if company_already_exists:
                # Company already exists in the array - reactivate it instead of duplicating
                # Mark all other companies as inactive
                for idx, existing_company in enumerate(existing_companies):
                    if isinstance(existing_company, dict):
                        if idx != existing_company_index:
                            existing_company["isCompanyActive"] = False
                        else:
                            # Reactivate the existing company entry
                            existing_company["isCompanyActive"] = True
                            # Update name in case it changed
                            existing_company["name"] = company_ref.get("name", existing_company.get("name"))
            else:
                # Company doesn't exist - add it as new
                # Mark all existing companies as inactive (historical)
                for existing_company in existing_companies:
                    if isinstance(existing_company, dict):
                        existing_company["isCompanyActive"] = False
                
                # Add new company as active
                company_ref["isCompanyActive"] = True
                existing_companies.append(company_ref)
            
            # Update parceiro
            update_dict = {
                "company": existing_companies,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(parceiro_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Parceiro(**result)
            return None
        except Exception as e:
            logger.error(f"Error linking company to parceiro: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def update_company_active_status(company_id: ObjectId, is_company_active: bool) -> int:
        """
        Updates the isCompanyActive field for all parceiros that belong to this company.
        Handles both old format (single object) and new format (array).
        
        Args:
            company_id: Company ObjectId
            is_company_active: New active status for the company
            
        Returns:
            Number of parceiros updated
        """
        collection = ParceiroRepository.get_collection()
        
        try:
            # Find all parceiros that have this company (both formats)
            parceiros_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            parceiros_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate
            all_parceiros = {}
            for parceiro in parceiros_array:
                all_parceiros[str(parceiro["_id"])] = parceiro
            for parceiro in parceiros_single:
                all_parceiros[str(parceiro["_id"])] = parceiro
            
            updated_count = 0
            for parceiro_doc in all_parceiros.values():
                updated = False
                
                if "company" in parceiro_doc:
                    # Handle array format
                    if isinstance(parceiro_doc["company"], list):
                        # Count how many companies exist
                        has_multiple_companies = len(parceiro_doc["company"]) > 1
                        
                        for company in parceiro_doc["company"]:
                            if isinstance(company, dict):
                                company_id_in_doc = company.get("id")
                                if company_id_in_doc:
                                    company_matches = False
                                    if isinstance(company_id_in_doc, ObjectId):
                                        company_matches = (company_id_in_doc == company_id)
                                    elif str(company_id_in_doc) == str(company_id):
                                        company_matches = True
                                    
                                    if company_matches:
                                        # If parceiro has only one company (or this is the only active one), always update
                                        # If parceiro has multiple companies, only update the active one (preserve historical)
                                        current_is_active = company.get("isCompanyActive", True)
                                        if not has_multiple_companies or current_is_active:
                                            company["isCompanyActive"] = is_company_active
                                            updated = True
                    
                    # Handle single object format
                    # Always update single object format (it's the only company)
                    elif isinstance(parceiro_doc["company"], dict):
                        company_id_in_doc = parceiro_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Single object format - always update (it's the only company)
                                parceiro_doc["company"]["isCompanyActive"] = is_company_active
                                updated = True
                
                if updated:
                    await collection.update_one(
                        {"_id": parceiro_doc["_id"]},
                        {
                            "$set": {
                                "company": parceiro_doc["company"],
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated isCompanyActive to {is_company_active} for {updated_count} parceiro(s) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating company active status in parceiros: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def update_license_type_by_company(company_id: ObjectId, new_license_type: str) -> int:
        """
        Updates the license type for all parceiros that belong to this company (active company only).
        Handles both old format (single object) and new format (array).
        Only updates parceiros with the company as active (isCompanyActive=True).
        
        Args:
            company_id: Company ObjectId
            new_license_type: New license type (Start or Hub)
            
        Returns:
            Number of parceiros updated
        """
        collection = ParceiroRepository.get_collection()
        
        try:
            # Find all parceiros that have this company (both formats: array and single object)
            # Query for array format
            parceiros_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            # Query for single object format (backward compatibility)
            parceiros_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate by _id
            all_parceiros = {}
            for parceiro in parceiros_array:
                all_parceiros[str(parceiro["_id"])] = parceiro
            for parceiro in parceiros_single:
                all_parceiros[str(parceiro["_id"])] = parceiro
            
            updated_count = 0
            for parceiro_doc in all_parceiros.values():
                should_update = False
                
                if "company" in parceiro_doc:
                    # Handle array format
                    if isinstance(parceiro_doc["company"], list):
                        for company in parceiro_doc["company"]:
                            if isinstance(company, dict):
                                company_id_in_doc = company.get("id")
                                if company_id_in_doc:
                                    company_matches = False
                                    if isinstance(company_id_in_doc, ObjectId):
                                        company_matches = (company_id_in_doc == company_id)
                                    elif str(company_id_in_doc) == str(company_id):
                                        company_matches = True
                                    
                                    if company_matches:
                                        # Only update if the company is currently active
                                        # Don't update historical companies (isCompanyActive: false)
                                        current_is_active = company.get("isCompanyActive", True)
                                        if current_is_active:
                                            should_update = True
                                            break
                    
                    # Handle single object format (backward compatibility)
                    elif isinstance(parceiro_doc["company"], dict):
                        company_id_in_doc = parceiro_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Only update if the company is currently active
                                current_is_active = parceiro_doc["company"].get("isCompanyActive", True)
                                if current_is_active:
                                    should_update = True
                
                if should_update:
                    await collection.update_one(
                        {"_id": parceiro_doc["_id"]},
                        {
                            "$set": {
                                "license_type": new_license_type,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated license type to '{new_license_type}' for {updated_count} parceiro(s) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating license type by company in parceiros: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def unlink_company(parceiro_id: str) -> Optional[Parceiro]:
        """
        Unlinks a company from a Parceiro by removing it from the company array.
        Prioritizes removing the active company (isCompanyActive=True) if it exists.
        If no active company exists, removes the first company in the array.
        The company doesn't need to be active to be unlinked.
        
        Args:
            parceiro_id: Parceiro ID
            
        Returns:
            Updated Parceiro or None if not found
        """
        collection = ParceiroRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                return None
            
            # Get current parceiro
            parceiro = await ParceiroRepository.get_by_id(parceiro_id)
            if not parceiro:
                raise ValueError("Parceiro não encontrado")
            
            # Normalize existing companies to list of dicts
            existing_companies = []
            if parceiro.company:
                if isinstance(parceiro.company, list):
                    for company_item in parceiro.company:
                        if hasattr(company_item, "model_dump"):
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(parceiro.company, dict):
                    if hasattr(parceiro.company, "model_dump"):
                        existing_companies.append(parceiro.company.model_dump())
                    else:
                        existing_companies.append(parceiro.company.copy())
                elif isinstance(parceiro.company, str):
                    existing_ref = await TeamRepository.resolve_company_reference(parceiro.company, validate_status=False)
                    if existing_ref:
                        existing_companies.append(existing_ref)
            
            if not existing_companies:
                raise ValueError("Nenhuma empresa vinculada para desvincular")
            
            # Find and remove company (prioritize active, but remove any if no active exists)
            company_removed = False
            updated_companies = []
            
            # First pass: remove active company if exists
            for company in existing_companies:
                if isinstance(company, dict):
                    is_active = company.get("isCompanyActive", True)
                    if is_active and not company_removed:
                        # Remove this active company
                        company_removed = True
                    else:
                        # Keep this company
                        updated_companies.append(company)
                else:
                    # Keep non-dict items (shouldn't happen, but just in case)
                    if not company_removed:
                        # Remove first non-dict item if no active company was found
                        company_removed = True
                    else:
                        updated_companies.append(company)
            
            # If no active company was found, remove the first company
            if not company_removed and existing_companies:
                # Remove first company
                updated_companies = existing_companies[1:]
                company_removed = True
            
            if not company_removed:
                raise ValueError("Nenhuma empresa encontrada para desvincular")
            
            # Update parceiro
            update_dict = {
                "company": updated_companies,
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(parceiro_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                # Normalize company field for backward compatibility
                if "company" in result and result["company"] is not None:
                    result["company"] = normalize_company_array_field(result["company"])
                return Parceiro(**result)
            return None
        except Exception as e:
            logger.error(f"Error unlinking company from parceiro: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
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
        return Database.get_database()["deal"]
    
    @staticmethod
    async def create(negocio: NegocioCreate, parceiro_id: str) -> Negocio:
        """Creates a new Negocio linked to a Parceiro."""
        collection = NegocioRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(parceiro_id):
                raise ValueError("Invalid parceiro_id")
            
            negocio_dict = negocio.model_dump()
            negocio_dict["parceiro_id"] = ObjectId(parceiro_id)
            negocio_dict["created_at"] = datetime.now(timezone.utc)
            negocio_dict["updated_at"] = datetime.now(timezone.utc)
            
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
            
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
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

