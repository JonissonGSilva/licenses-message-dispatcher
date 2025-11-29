"""Repository for Company operations."""
from typing import Dict, List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.company import Company, CompanyCreate, CompanyUpdate
import logging

logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository for managing companies in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the companies collection."""
        return Database.get_database()["companies"]
    
    @staticmethod
    async def create(company: CompanyCreate) -> Company:
        """Creates a new company."""
        collection = CompanyRepository.get_collection()
        
        try:
            company_dict = company.model_dump()
            company_dict["created_at"] = datetime.utcnow()
            company_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating company in database: {company.name}")
            result = await collection.insert_one(company_dict)
            company_dict["_id"] = result.inserted_id
            
            company_created = Company(**company_dict)
            logger.info(f"Company created successfully: ID={result.inserted_id}, Name={company.name}")
            return company_created
        except Exception as e:
            logger.error(f"Error creating company in database: {type(e).__name__}: {e}")
            logger.error(f"Company data: {company.model_dump()}", exc_info=True)
            raise
    
    @staticmethod
    async def create_many(companies: List[CompanyCreate]) -> List[Company]:
        """Creates multiple companies."""
        collection = CompanyRepository.get_collection()
        
        companies_dict = []
        now = datetime.utcnow()
        
        for company in companies:
            company_dict = company.model_dump()
            company_dict["created_at"] = now
            company_dict["updated_at"] = now
            companies_dict.append(company_dict)
        
        if not companies_dict:
            logger.warning("No companies to create")
            return []
        
        try:
            logger.info(f"Inserting {len(companies_dict)} companies into database...")
            result = await collection.insert_many(companies_dict)
            logger.info(f"Companies inserted into database: {len(result.inserted_ids)} documents")
            
            inserted_ids = result.inserted_ids
            companies_created = []
            
            for i, inserted_id in enumerate(inserted_ids):
                company_dict = companies_dict[i].copy()
                company_dict["_id"] = inserted_id
                try:
                    company_created = Company(**company_dict)
                    companies_created.append(company_created)
                    logger.debug(f"Company {i+1}/{len(inserted_ids)} created: ID={inserted_id}, Name={company_dict.get('name', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error creating Company model for document {i+1}: {type(e).__name__}: {e}")
                    logger.error(f"Inserted ID: {inserted_id}")
                    logger.error(f"Document data: {company_dict}")
                    logger.error(f"Error details:", exc_info=True)
                    raise
            
            logger.info(f"All {len(companies_created)} companies were created successfully")
            return companies_created
        except Exception as e:
            logger.error(f"Error creating multiple companies: {type(e).__name__}: {e}")
            logger.error(f"Total companies attempted: {len(companies_dict)}", exc_info=True)
            raise
    
    @staticmethod
    async def find_by_id(company_id: str) -> Optional[Company]:
        """Finds a company by ID."""
        collection = CompanyRepository.get_collection()
        
        company = await collection.find_one({"_id": ObjectId(company_id)})
        return Company(**company) if company else None
    
    @staticmethod
    async def find_by_cnpj(cnpj: str) -> Optional[Company]:
        """Finds a company by CNPJ."""
        collection = CompanyRepository.get_collection()
        
        company = await collection.find_one({"cnpj": cnpj})
        return Company(**company) if company else None
    
    @staticmethod
    async def find_by_name(name: str) -> Optional[Company]:
        """Finds a company by name."""
        collection = CompanyRepository.get_collection()
        
        company = await collection.find_one({"name": name})
        return Company(**company) if company else None
    
    @staticmethod
    async def find_by_portal_id(portal_id: str) -> Optional[Company]:
        """Finds a company by portal ID."""
        collection = CompanyRepository.get_collection()
        
        company = await collection.find_one({"portal_id": portal_id})
        return Company(**company) if company else None
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Company]:
        """Lists all companies."""
        collection = CompanyRepository.get_collection()
        
        cursor = collection.find().skip(skip).limit(limit)
        companies = await cursor.to_list(length=None)
        
        return [Company(**c) for c in companies]
    
    @staticmethod
    async def list_by_filter(
        active: Optional[bool] = None,
        linked: Optional[bool] = None,
        license_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """Lists companies with optional filters."""
        collection = CompanyRepository.get_collection()
        
        filter_dict = {}
        if active is not None:
            filter_dict["active"] = active
        if linked is not None:
            filter_dict["linked"] = linked
        if license_type:
            filter_dict["license_type"] = license_type
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit)
        companies = await cursor.to_list(length=None)
        
        return [Company(**c) for c in companies]
    
    @staticmethod
    async def update(company_id: str, company_update: CompanyUpdate) -> Optional[Company]:
        """Updates a company."""
        collection = CompanyRepository.get_collection()
        
        update_dict = company_update.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"_id": ObjectId(company_id)},
                {"$set": update_dict}
            )
        
        return await CompanyRepository.find_by_id(company_id)
    
    @staticmethod
    async def add_contract_renovated(
        company_id: str,
        age_contract: int,
        type_contract: int,
        is_expirated: bool = False
    ) -> Optional[Company]:
        """
        Adds a new contract renovation record to the company's contract_renovated array.
        
        Args:
            company_id: Company ID
            age_contract: Age of the contract
            type_contract: Type of contract
            is_expirated: Whether the contract is expired
            
        Returns:
            Updated Company or None if not found
        """
        collection = CompanyRepository.get_collection()
        now = datetime.utcnow()
        
        contract_record = {
            "age_contract": age_contract,
            "type_contract": type_contract,
            "isExpirated": is_expirated,
            "created_at": now,
            "updated_at": now
        }
        
        # Add to array and update updated_at
        await collection.update_one(
            {"_id": ObjectId(company_id)},
            {
                "$push": {"contract_renovated": contract_record},
                "$set": {"updated_at": now}
            }
        )
        
        return await CompanyRepository.find_by_id(company_id)
    
    @staticmethod
    async def mark_latest_contract_expired(company_id: str) -> Optional[Company]:
        """
        Marks the most recent contract in contract_renovated array as expired.
        
        Args:
            company_id: Company ID
            
        Returns:
            Updated Company or None if not found
        """
        collection = CompanyRepository.get_collection()
        now = datetime.utcnow()
        
        # Get current company to find the latest contract
        company = await CompanyRepository.find_by_id(company_id)
        if not company or not company.contract_renovated:
            return company
        
        # Find the index of the most recent contract (last in array)
        # Since we're using $push, the last element is the most recent
        contract_count = len(company.contract_renovated)
        if contract_count == 0:
            return company
        
        # Update the last contract's isExpirated to true
        # Using array index notation: contract_renovated.<index>
        last_index = contract_count - 1
        
        await collection.update_one(
            {"_id": ObjectId(company_id)},
            {
                "$set": {
                    f"contract_renovated.{last_index}.isExpirated": True,
                    f"contract_renovated.{last_index}.updated_at": now,
                    "updated_at": now
                }
            }
        )
        
        return await CompanyRepository.find_by_id(company_id)
    
    @staticmethod
    async def set_is_active(company_id: str, is_active: bool) -> Optional[Company]:
        """
        Sets the isActive field on the company.
        
        Args:
            company_id: Company ID
            is_active: Active status
            
        Returns:
            Updated Company or None if not found
        """
        collection = CompanyRepository.get_collection()
        
        await collection.update_one(
            {"_id": ObjectId(company_id)},
            {
                "$set": {
                    "isActive": is_active,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return await CompanyRepository.find_by_id(company_id)
    
    @staticmethod
    async def delete(company_id: str) -> bool:
        """Deletes a company."""
        collection = CompanyRepository.get_collection()
        
        result = await collection.delete_one({"_id": ObjectId(company_id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def count(filter_dict: dict = None) -> int:
        """Counts companies based on a filter."""
        collection = CompanyRepository.get_collection()
        
        if filter_dict is None:
            filter_dict = {}
        
        return await collection.count_documents(filter_dict)
    
    @staticmethod
    async def check_duplicates(companies: List[CompanyCreate]) -> Dict[str, Company]:
        """
        Checks for duplicate companies by CNPJ, name, or portal_id.
        
        Args:
            companies: List of CompanyCreate to check
            
        Returns:
            Dict mapping CNPJ/name/portal_id to existing Company if duplicate found
        """
        collection = CompanyRepository.get_collection()
        duplicates = {}
        
        # Get all CNPJs, names, and portal_ids from the list
        cnpjs = [c.cnpj for c in companies if c.cnpj and c.cnpj.strip()]
        names = [c.name for c in companies if c.name and c.name.strip()]
        portal_ids = [c.portal_id for c in companies if c.portal_id and c.portal_id.strip()]
        
        # Check for duplicates by CNPJ
        if cnpjs:
            cursor = collection.find({"cnpj": {"$in": cnpjs}})
            existing_by_cnpj = await cursor.to_list(length=None)
            for existing in existing_by_cnpj:
                company = Company(**existing)
                duplicates[company.cnpj] = company
                logger.debug(f"Duplicate found by CNPJ: {company.cnpj} (ID: {company.id})")
        
        # Check for duplicates by name (only if not already found by CNPJ)
        if names:
            cursor = collection.find({"name": {"$in": names}})
            existing_by_name = await cursor.to_list(length=None)
            for existing in existing_by_name:
                company = Company(**existing)
                # Only add if not already found by CNPJ
                if company.cnpj not in duplicates:
                    duplicates[company.name] = company
                    logger.debug(f"Duplicate found by name: {company.name} (ID: {company.id})")
        
        # Check for duplicates by portal_id (only if not already found)
        if portal_ids:
            cursor = collection.find({"portal_id": {"$in": portal_ids}})
            existing_by_portal = await cursor.to_list(length=None)
            for existing in existing_by_portal:
                company = Company(**existing)
                # Only add if not already found by CNPJ or name
                if company.cnpj not in duplicates and company.name not in duplicates:
                    duplicates[company.portal_id] = company
                    logger.debug(f"Duplicate found by portal_id: {company.portal_id} (ID: {company.id})")
        
        logger.info(f"Found {len(duplicates)} duplicate(s) out of {len(companies)} companies to check")
        return duplicates

