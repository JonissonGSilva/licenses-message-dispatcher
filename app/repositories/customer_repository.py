"""Repository for Customer operations."""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.customer import Customer, CustomerCreate, CustomerUpdate
import logging

logger = logging.getLogger(__name__)


class CustomerRepository:
    """Repository for managing customers in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the customers collection."""
        return Database.get_database()["customers"]
    
    @staticmethod
    async def create(customer: CustomerCreate) -> Customer:
        """Creates a new customer."""
        collection = CustomerRepository.get_collection()
        
        try:
            customer_dict = customer.model_dump()
            customer_dict["created_at"] = datetime.utcnow()
            customer_dict["updated_at"] = datetime.utcnow()
            
            logger.debug(f"Creating customer in database: {customer.name} ({customer.phone})")
            result = await collection.insert_one(customer_dict)
            customer_dict["_id"] = result.inserted_id
            
            customer_created = Customer(**customer_dict)
            logger.info(f"Customer created successfully: ID={result.inserted_id}, Name={customer.name}")
            return customer_created
        except Exception as e:
            logger.error(f"Error creating customer in database: {type(e).__name__}: {e}")
            logger.error(f"Customer data: {customer.model_dump()}", exc_info=True)
            raise
    
    @staticmethod
    async def create_many(customers: List[CustomerCreate]) -> List[Customer]:
        """Creates multiple customers."""
        collection = CustomerRepository.get_collection()
        
        customers_dict = []
        now = datetime.utcnow()
        
        for customer in customers:
            customer_dict = customer.model_dump()
            customer_dict["created_at"] = now
            customer_dict["updated_at"] = now
            customers_dict.append(customer_dict)
        
        if not customers_dict:
            logger.warning("No customers to create")
            return []
        
        try:
            logger.info(f"Inserting {len(customers_dict)} customers into database...")
            # Insert documents
            result = await collection.insert_many(customers_dict)
            logger.info(f"Customers inserted into database: {len(result.inserted_ids)} documents")
            
            # Get inserted documents with correct IDs
            inserted_ids = result.inserted_ids
            customers_created = []
            
            for i, inserted_id in enumerate(inserted_ids):
                customer_dict = customers_dict[i].copy()
                customer_dict["_id"] = inserted_id
                try:
                    customer_created = Customer(**customer_dict)
                    customers_created.append(customer_created)
                    logger.debug(f"Customer {i+1}/{len(inserted_ids)} created: ID={inserted_id}, Name={customer_dict.get('name', 'N/A')}")
                except Exception as e:
                    logger.error(f"Error creating Customer model for document {i+1}: {type(e).__name__}: {e}")
                    logger.error(f"Inserted ID: {inserted_id}")
                    logger.error(f"Document data: {customer_dict}")
                    logger.error(f"Error details:", exc_info=True)
                    raise
            
            logger.info(f"All {len(customers_created)} customers were created successfully")
            return customers_created
        except Exception as e:
            logger.error(f"Error creating multiple customers: {type(e).__name__}: {e}")
            logger.error(f"Total customers attempted: {len(customers_dict)}", exc_info=True)
            raise
    
    @staticmethod
    async def find_by_id(customer_id: str) -> Optional[Customer]:
        """Finds a customer by ID."""
        collection = CustomerRepository.get_collection()
        
        customer = await collection.find_one({"_id": ObjectId(customer_id)})
        return Customer(**customer) if customer else None
    
    @staticmethod
    async def find_by_phone(phone: str) -> Optional[Customer]:
        """Finds a customer by phone."""
        collection = CustomerRepository.get_collection()
        
        customer = await collection.find_one({"phone": phone})
        return Customer(**customer) if customer else None
    
    @staticmethod
    async def find_by_email(email: str) -> Optional[Customer]:
        """Finds a customer by email."""
        collection = CustomerRepository.get_collection()
        
        customer = await collection.find_one({"email": email})
        return Customer(**customer) if customer else None
    
    @staticmethod
    async def list_by_license_type(license_type: str, active: bool = True) -> List[Customer]:
        """Lists customers by license type."""
        collection = CustomerRepository.get_collection()
        
        filter_dict = {"license_type": license_type}
        if active is not None:
            filter_dict["active"] = active
        
        cursor = collection.find(filter_dict)
        customers = await cursor.to_list(length=None)
        
        return [Customer(**c) for c in customers]
    
    @staticmethod
    async def update(customer_id: str, customer_update: CustomerUpdate) -> Optional[Customer]:
        """Updates a customer."""
        collection = CustomerRepository.get_collection()
        
        update_dict = customer_update.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": update_dict}
            )
        
        return await CustomerRepository.find_by_id(customer_id)
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Customer]:
        """Lists all customers."""
        collection = CustomerRepository.get_collection()
        
        cursor = collection.find().skip(skip).limit(limit)
        customers = await cursor.to_list(length=None)
        
        return [Customer(**c) for c in customers]
    
    @staticmethod
    async def count(filter_dict: dict = None) -> int:
        """Counts customers based on a filter."""
        collection = CustomerRepository.get_collection()
        
        if filter_dict is None:
            filter_dict = {}
        
        return await collection.count_documents(filter_dict)
    
    @staticmethod
    async def check_duplicates(customers: List[CustomerCreate]) -> Dict[str, Customer]:
        """
        Checks for duplicate customers by phone or email.
        
        Args:
            customers: List of CustomerCreate to check
            
        Returns:
            Dict mapping phone/email to existing Customer if duplicate found
        """
        collection = CustomerRepository.get_collection()
        duplicates = {}
        
        # Get all phones and emails from the list
        phones = [c.phone for c in customers if c.phone]
        emails = [c.email for c in customers if c.email and c.email.strip()]
        
        # Check for duplicates by phone
        if phones:
            cursor = collection.find({"phone": {"$in": phones}})
            existing_by_phone = await cursor.to_list(length=None)
            for existing in existing_by_phone:
                customer = Customer(**existing)
                duplicates[customer.phone] = customer
                logger.debug(f"Duplicate found by phone: {customer.phone} (ID: {customer.id})")
        
        # Check for duplicates by email (only if email is provided and not already found by phone)
        if emails:
            cursor = collection.find({"email": {"$in": emails}})
            existing_by_email = await cursor.to_list(length=None)
            for existing in existing_by_email:
                customer = Customer(**existing)
                # Only add if not already found by phone
                if customer.phone not in duplicates:
                    duplicates[customer.email] = customer
                    logger.debug(f"Duplicate found by email: {customer.email} (ID: {customer.id})")
        
        logger.info(f"Found {len(duplicates)} duplicate(s) out of {len(customers)} customers to check")
        return duplicates

