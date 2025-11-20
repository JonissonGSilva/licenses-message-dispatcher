"""Repository for Message operations."""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.message import Message, MessageCreate, MessageUpdate
import logging

logger = logging.getLogger(__name__)


class MessageRepository:
    """Repository for managing messages in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the messages collection."""
        return Database.get_database()["messages"]
    
    @staticmethod
    async def create(message: MessageCreate) -> Message:
        """Creates a new message."""
        collection = MessageRepository.get_collection()
        
        message_dict = message.model_dump()
        message_dict["created_at"] = datetime.utcnow()
        message_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(message_dict)
        message_dict["_id"] = result.inserted_id
        
        return Message(**message_dict)
    
    @staticmethod
    async def create_many(messages: List[MessageCreate]) -> List[Message]:
        """Creates multiple messages."""
        collection = MessageRepository.get_collection()
        
        messages_dict = []
        now = datetime.utcnow()
        
        for message in messages:
            message_dict = message.model_dump()
            message_dict["created_at"] = now
            message_dict["updated_at"] = now
            messages_dict.append(message_dict)
        
        if messages_dict:
            await collection.insert_many(messages_dict)
        
        return [Message(**m) for m in messages_dict]
    
    @staticmethod
    async def find_by_id(message_id: str) -> Optional[Message]:
        """Finds a message by ID."""
        collection = MessageRepository.get_collection()
        
        message = await collection.find_one({"_id": ObjectId(message_id)})
        return Message(**message) if message else None
    
    @staticmethod
    async def update(message_id: str, message_update: MessageUpdate) -> Optional[Message]:
        """Updates a message."""
        collection = MessageRepository.get_collection()
        
        update_dict = message_update.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": update_dict}
            )
        
        return await MessageRepository.find_by_id(message_id)
    
    @staticmethod
    async def list_by_status(status: str, skip: int = 0, limit: int = 100) -> List[Message]:
        """Lists messages by status."""
        collection = MessageRepository.get_collection()
        
        cursor = collection.find({"status": status}).skip(skip).limit(limit)
        messages = await cursor.to_list(length=None)
        
        return [Message(**m) for m in messages]
    
    @staticmethod
    async def list_by_customer(customer_id: str, skip: int = 0, limit: int = 100) -> List[Message]:
        """Lists messages by customer."""
        collection = MessageRepository.get_collection()
        
        cursor = collection.find({"customer_id": ObjectId(customer_id)}).skip(skip).limit(limit)
        messages = await cursor.to_list(length=None)
        
        return [Message(**m) for m in messages]
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Message]:
        """Lists all messages."""
        collection = MessageRepository.get_collection()
        
        cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
        messages = await cursor.to_list(length=None)
        
        return [Message(**m) for m in messages]

