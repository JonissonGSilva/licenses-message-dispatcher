"""Repository for License operations."""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.license import License, LicenseCreate, LicenseUpdate
import logging

logger = logging.getLogger(__name__)


class LicenseRepository:
    """Repository for managing licenses in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the licenses collection."""
        return Database.get_database()["licenses"]
    
    @staticmethod
    async def create(license: LicenseCreate) -> License:
        """Creates a new license."""
        collection = LicenseRepository.get_collection()
        
        license_dict = license.model_dump()
        license_dict["created_at"] = datetime.utcnow()
        license_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(license_dict)
        license_dict["_id"] = result.inserted_id
        
        return License(**license_dict)
    
    @staticmethod
    async def find_by_id(license_id: str) -> Optional[License]:
        """Finds a license by ID."""
        collection = LicenseRepository.get_collection()
        
        license = await collection.find_one({"_id": ObjectId(license_id)})
        return License(**license) if license else None
    
    @staticmethod
    async def find_by_portal_id(portal_id: str) -> Optional[License]:
        """Finds a license by Portal ID."""
        collection = LicenseRepository.get_collection()
        
        license = await collection.find_one({"portal_id": portal_id})
        return License(**license) if license else None
    
    @staticmethod
    async def find_by_customer_id(customer_id: str) -> List[License]:
        """Finds licenses by customer ID."""
        collection = LicenseRepository.get_collection()
        
        cursor = collection.find({"customer_id": ObjectId(customer_id)})
        licenses = await cursor.to_list(length=None)
        
        return [License(**l) for l in licenses]
    
    @staticmethod
    async def update(license_id: str, license_update: LicenseUpdate) -> Optional[License]:
        """Updates a license."""
        collection = LicenseRepository.get_collection()
        
        update_dict = license_update.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"_id": ObjectId(license_id)},
                {"$set": update_dict}
            )
        
        return await LicenseRepository.find_by_id(license_id)
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[License]:
        """Lists all licenses."""
        collection = LicenseRepository.get_collection()
        
        cursor = collection.find().skip(skip).limit(limit)
        licenses = await cursor.to_list(length=None)
        
        return [License(**l) for l in licenses]

