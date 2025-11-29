"""Repository for Company History operations."""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.company_history import CompanyHistory, CompanyHistoryCreate
import logging

logger = logging.getLogger(__name__)


class CompanyHistoryRepository:
    """Repository for managing company history in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the company_history collection."""
        return Database.get_database()["company_history"]
    
    @staticmethod
    async def create(history: CompanyHistoryCreate) -> CompanyHistory:
        """Creates a new history entry."""
        collection = CompanyHistoryRepository.get_collection()
        
        try:
            history_dict = {
                "company_id": ObjectId(history.company_id),
                "action": history.action,
                "changes": history.changes,
                "user": history.user,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            logger.debug(f"Creating history entry for company: {history.company_id}")
            result = await collection.insert_one(history_dict)
            history_dict["_id"] = result.inserted_id
            
            history_created = CompanyHistory(**history_dict)
            logger.info(f"History entry created successfully: ID={result.inserted_id}, Company={history.company_id}")
            return history_created
        except Exception as e:
            logger.error(f"Error creating history entry: {type(e).__name__}: {e}")
            logger.error(f"History data: {history.model_dump()}", exc_info=True)
            raise
    
    @staticmethod
    async def list_by_company(company_id: str, skip: int = 0, limit: int = 100) -> List[CompanyHistory]:
        """Lists history entries for a company."""
        collection = CompanyHistoryRepository.get_collection()
        
        try:
            cursor = collection.find({"company_id": ObjectId(company_id)}).sort("timestamp", -1).skip(skip).limit(limit)
            histories = await cursor.to_list(length=None)
            
            return [CompanyHistory(**h) for h in histories]
        except Exception as e:
            logger.error(f"Error listing history for company {company_id}: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    async def find_by_id(history_id: str) -> Optional[CompanyHistory]:
        """Finds a history entry by ID."""
        collection = CompanyHistoryRepository.get_collection()
        
        history = await collection.find_one({"_id": ObjectId(history_id)})
        return CompanyHistory(**history) if history else None


