"""Repository for Customer operations."""
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from app.database import Database
from app.models.customer import Customer, CustomerCreate, CustomerUpdate
from app.repositories.company_repository import CompanyRepository
import logging
import copy

logger = logging.getLogger(__name__)


class CustomerRepository:
    """Repository for managing customers in MongoDB."""
    
    @staticmethod
    def get_collection():
        """Returns the customers collection."""
        return Database.get_database()["customers"]
    
    @staticmethod
    def get_active_company(company_value: Any) -> Optional[Dict[str, Any]]:
        """
        Gets the active company from company field (array or single value).
        Only returns company with isCompanyActive=True.
        
        Args:
            company_value: Company value (can be list, dict, str, or None)
            
        Returns:
            Dict with company reference if active company found, None otherwise
        """
        if not company_value:
            return None
        
        # If it's a list, find the active one
        if isinstance(company_value, list):
            for company in company_value:
                if isinstance(company, dict):
                    # Check if company is active (default to True if not specified for backward compatibility)
                    is_active = company.get("isCompanyActive", True)
                    if is_active:
                        return company
            return None
        
        # If it's a single dict, check if active
        if isinstance(company_value, dict):
            is_active = company_value.get("isCompanyActive", True)
            if is_active:
                return company_value
            return None
        
        # If it's a string, return None (needs to be resolved)
        return None
    
    @staticmethod
    async def resolve_company_reference(company_name: Optional[str], validate_status: bool = True) -> Optional[Dict[str, Any]]:
        """
        Resolves a company name to a company reference (id and name).
        
        Args:
            company_name: Company name to search for
            validate_status: If True, validates that company is active=True
            
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
                # Store ObjectId directly, not as string, so MongoDB queries work
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
    
    @staticmethod
    async def create(customer: CustomerCreate) -> Customer:
        """Creates a new customer."""
        collection = CustomerRepository.get_collection()
        
        try:
            customer_dict = customer.model_dump()
            
            # Normalize company field - handle both old (single) and new (array) formats
            # Only one company can be active at a time
            companies_list = []
            if customer.company:
                # If it's a list, process each item (only first one will be active)
                if isinstance(customer.company, list):
                    for idx, company_item in enumerate(customer.company):
                        if isinstance(company_item, str):
                            company_ref = await CustomerRepository.resolve_company_reference(company_item, validate_status=True)
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
                elif isinstance(customer.company, str):
                    company_ref = await CustomerRepository.resolve_company_reference(customer.company, validate_status=True)
                    if company_ref:
                        company_ref["isCompanyActive"] = True  # First and only company is active
                        companies_list.append(company_ref)
                    else:
                        raise ValueError(f"Company '{customer.company}' not found or is not active. Company must exist in Companies collection with active=true")
                elif isinstance(customer.company, dict):
                    company_dict = customer.company.copy()
                    company_dict["isCompanyActive"] = True  # First and only company is active
                    companies_list.append(company_dict)
            
            customer_dict["company"] = companies_list
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
        
        # Resolve all company references first (batch processing for better performance)
        company_names = set()
        for customer in customers:
            if customer.company and isinstance(customer.company, str) and customer.company.strip():
                company_names.add(customer.company.strip())
        
        # Batch lookup companies (validate that they are active)
        company_cache = {}
        if company_names:
            logger.debug(f"Resolving {len(company_names)} unique company names...")
            for company_name in company_names:
                company_ref = await CustomerRepository.resolve_company_reference(company_name, validate_status=True)
                if company_ref:
                    company_cache[company_name] = company_ref
        
        # Process customers with resolved company references
        for customer in customers:
            customer_dict = customer.model_dump()
            
            # Resolve company reference if company name is provided
            # Validate that company exists and is active
            # Only one company can be active at a time
            if customer.company and isinstance(customer.company, str):
                company_name = customer.company.strip()
                if company_name in company_cache:
                    company_ref = company_cache[company_name].copy()
                    company_ref["isCompanyActive"] = True  # First and only company is active
                    customer_dict["company"] = [company_ref]  # Store as array
                    logger.debug(f"Company reference resolved: {company_ref['name']} (ID: {company_ref['id']})")
                else:
                    # If company not found or invalid, skip this customer
                    # This should have been validated in CSV processing, but double-check here
                    logger.warning(f"Company '{company_name}' not found or is not active. Skipping customer '{customer.name}'.")
                    continue  # Skip this customer
            else:
                customer_dict["company"] = []  # Empty array if no company
            
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
        
        if not ObjectId.is_valid(customer_id):
            return None
        
        customer = await collection.find_one({"_id": ObjectId(customer_id)})
        if customer:
            # Normalize company field for backward compatibility
            from app.models.customer import normalize_company_array_field
            if "company" in customer and customer["company"] is not None:
                customer["company"] = normalize_company_array_field(customer["company"])
            return Customer(**customer)
        return None
    
    @staticmethod
    async def find_by_phone(phone: str) -> Optional[Customer]:
        """Finds a customer by phone."""
        collection = CustomerRepository.get_collection()
        
        customer = await collection.find_one({"phone": phone})
        if customer:
            # Normalize company field for backward compatibility
            from app.models.customer import normalize_company_array_field
            if "company" in customer and customer["company"] is not None:
                customer["company"] = normalize_company_array_field(customer["company"])
            return Customer(**customer)
        return None
    
    @staticmethod
    async def find_by_email(email: str) -> Optional[Customer]:
        """Finds a customer by email."""
        collection = CustomerRepository.get_collection()
        
        customer = await collection.find_one({"email": email})
        if customer:
            # Normalize company field for backward compatibility
            from app.models.customer import normalize_company_array_field
            if "company" in customer and customer["company"] is not None:
                customer["company"] = normalize_company_array_field(customer["company"])
            return Customer(**customer)
        return None
    
    @staticmethod
    async def list_by_license_type(license_type: str, active: bool = True) -> List[Customer]:
        """Lists customers by license type."""
        collection = CustomerRepository.get_collection()
        
        filter_dict = {"license_type": license_type}
        if active is not None:
            filter_dict["active"] = active
        
        cursor = collection.find(filter_dict)
        customers_docs = await cursor.to_list(length=None)
        
        # Normalize company field for backward compatibility
        from app.models.customer import normalize_company_array_field
        normalized_customers = []
        for c in customers_docs:
            if "company" in c and c["company"] is not None:
                c["company"] = normalize_company_array_field(c["company"])
            normalized_customers.append(Customer(**c))
        
        return normalized_customers
    
    @staticmethod
    async def list_by_company(company_id: ObjectId, active: Optional[bool] = None, skip: int = 0, limit: int = 100) -> List[Customer]:
        """
        Lists customers by company ID. Only considers active companies (isCompanyActive=True).
        
        Args:
            company_id: Company ObjectId
            active: Optional filter for active status (True/False)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Customer objects
        """
        collection = CustomerRepository.get_collection()
        
        # Use $elemMatch to find customers where company array contains this company_id with isCompanyActive=True
        filter_dict = {
            "company": {
                "$elemMatch": {
                    "id": company_id,
                    "isCompanyActive": True
                }
            }
        }
        if active is not None:
            filter_dict["active"] = active
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit)
        customers_docs = await cursor.to_list(length=None)
        
        # Normalize company field for backward compatibility
        from app.models.customer import normalize_company_array_field
        normalized_customers = []
        for c in customers_docs:
            if "company" in c and c["company"] is not None:
                c["company"] = normalize_company_array_field(c["company"])
            normalized_customers.append(Customer(**c))
        
        return normalized_customers
    
    @staticmethod
    async def update(customer_id: str, customer_update: CustomerUpdate) -> Optional[Customer]:
        """Updates a customer."""
        collection = CustomerRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(customer_id):
                return None
            
            update_dict = customer_update.model_dump(exclude_unset=True)
            
            # Normalize company field if provided
            # Only one company can be active at a time
            if "company" in update_dict and update_dict["company"] is not None:
                companies_list = []
                if isinstance(update_dict["company"], list):
                    for idx, company_item in enumerate(update_dict["company"]):
                        if isinstance(company_item, str):
                            company_ref = await CustomerRepository.resolve_company_reference(company_item, validate_status=True)
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
                    company_ref = await CustomerRepository.resolve_company_reference(update_dict["company"], validate_status=True)
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
            
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()
                await collection.update_one(
                    {"_id": ObjectId(customer_id)},
                    {"$set": update_dict}
                )
            
            return await CustomerRepository.find_by_id(customer_id)
        except Exception as e:
            logger.error(f"Error updating customer: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def link_company(customer_id: str, company_name: str) -> Optional[Customer]:
        """
        Links a company to a Customer. 
        - Validates that the company is not already linked (as active)
        - Marks previous active company as inactive (isCompanyActive=False)
        - Only one company can be active at a time
        """
        collection = CustomerRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(customer_id):
                return None
            
            # Resolve company reference
            company_ref = await CustomerRepository.resolve_company_reference(company_name, validate_status=True)
            if not company_ref:
                raise ValueError(f"Company '{company_name}' not found or is not active")
            
            # Get current customer
            customer = await CustomerRepository.find_by_id(customer_id)
            if not customer:
                raise ValueError("Cliente não encontrado")
            
            # Normalize existing companies to list
            # Convert to dicts to avoid Pydantic model serialization issues
            existing_companies = []
            if customer.company:
                if isinstance(customer.company, list):
                    for company_item in customer.company:
                        if hasattr(company_item, "model_dump"):
                            # Convert Pydantic model to dict
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(customer.company, dict):
                    if hasattr(customer.company, "model_dump"):
                        existing_companies.append(customer.company.model_dump())
                    else:
                        existing_companies.append(customer.company.copy())
                elif isinstance(customer.company, str):
                    # Try to resolve existing company
                    existing_ref = await CustomerRepository.resolve_company_reference(customer.company, validate_status=False)
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
                            raise ValueError(f"Company '{company_name}' is already linked as active to this customer")
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
                
                # Add new company as active (ensure it's a dict, not a Pydantic model)
                company_ref_dict = company_ref.copy() if isinstance(company_ref, dict) else company_ref
                company_ref_dict["isCompanyActive"] = True
                existing_companies.append(company_ref_dict)
            
            # Update customer
            # Also update license_type based on company's license_type
            update_dict = {
                "company": existing_companies,
                "updated_at": datetime.utcnow()
            }
            
            # Update license_type if company has license_type
            if "license_type" in company_ref and company_ref["license_type"]:
                update_dict["license_type"] = company_ref["license_type"]
            
            await collection.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": update_dict}
            )
            
            return await CustomerRepository.find_by_id(customer_id)
        except Exception as e:
            logger.error(f"Error linking company to customer: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def unlink_company(customer_id: str) -> Optional[Customer]:
        """
        Unlinks a company from a Customer by removing it from the company array.
        Prioritizes removing the active company (isCompanyActive=True) if it exists.
        If no active company exists, removes the first company in the array.
        The company doesn't need to be active to be unlinked.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Updated Customer or None if not found
        """
        collection = CustomerRepository.get_collection()
        
        try:
            if not ObjectId.is_valid(customer_id):
                return None
            
            # Get current customer
            customer = await CustomerRepository.find_by_id(customer_id)
            if not customer:
                raise ValueError("Cliente não encontrado")
            
            # Normalize existing companies to list of dicts
            existing_companies = []
            if customer.company:
                if isinstance(customer.company, list):
                    for company_item in customer.company:
                        if hasattr(company_item, "model_dump"):
                            existing_companies.append(company_item.model_dump())
                        elif isinstance(company_item, dict):
                            existing_companies.append(company_item.copy())
                        else:
                            existing_companies.append(company_item)
                elif isinstance(customer.company, dict):
                    if hasattr(customer.company, "model_dump"):
                        existing_companies.append(customer.company.model_dump())
                    else:
                        existing_companies.append(customer.company.copy())
                elif isinstance(customer.company, str):
                    existing_ref = await CustomerRepository.resolve_company_reference(customer.company, validate_status=False)
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
            
            # Update customer
            update_dict = {
                "company": updated_companies,
                "updated_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": update_dict}
            )
            
            return await CustomerRepository.find_by_id(customer_id)
        except Exception as e:
            logger.error(f"Error unlinking company from customer: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def list_all(skip: int = 0, limit: int = 100) -> List[Customer]:
        """Lists all customers."""
        collection = CustomerRepository.get_collection()
        
        cursor = collection.find().skip(skip).limit(limit)
        customers_docs = await cursor.to_list(length=None)
        
        # Normalize company field for backward compatibility
        from app.models.customer import normalize_company_array_field
        normalized_customers = []
        for c in customers_docs:
            # Normalize company field if it exists
            if "company" in c and c["company"] is not None:
                c["company"] = normalize_company_array_field(c["company"])
            normalized_customers.append(Customer(**c))
        
        return normalized_customers
    
    @staticmethod
    async def delete(customer_id: str) -> bool:
        """Deletes a customer."""
        collection = CustomerRepository.get_collection()
        
        result = await collection.delete_one({"_id": ObjectId(customer_id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def update_company_name(company_id: ObjectId, new_name: str) -> int:
        """
        Updates the company name in all customers that reference this company (in array).
        Updates all occurrences (active and inactive) for historical consistency.
        
        Args:
            company_id: Company ObjectId
            new_name: New company name
            
        Returns:
            Number of customers updated
        """
        collection = CustomerRepository.get_collection()
        
        try:
            # Find all customers that have this company in their array
            customers = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            updated_count = 0
            for customer_doc in customers:
                if "company" in customer_doc and isinstance(customer_doc["company"], list):
                    # Update name in all occurrences of this company
                    updated = False
                    for company in customer_doc["company"]:
                        if isinstance(company, dict):
                            company_id_in_doc = company.get("id")
                            # Compare ObjectId properly (handle both ObjectId and string)
                            if company_id_in_doc:
                                if isinstance(company_id_in_doc, ObjectId):
                                    if company_id_in_doc == company_id:
                                        company["name"] = new_name
                                        updated = True
                                elif str(company_id_in_doc) == str(company_id):
                                    company["name"] = new_name
                                    updated = True
                    
                    if updated:
                        await collection.update_one(
                            {"_id": customer_doc["_id"]},
                            {
                                "$set": {
                                    "company": customer_doc["company"],
                                    "updated_at": datetime.utcnow()
                                }
                            }
                        )
                        updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated company name to '{new_name}' in {updated_count} customer(s) for company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating company name: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def clear_company_reference(company_id: ObjectId) -> int:
        """
        Clears company reference from all customers that reference this company.
        Removes the company from the array (both active and inactive).
        
        Args:
            company_id: Company ObjectId to clear references for
            
        Returns:
            Number of customers updated
        """
        collection = CustomerRepository.get_collection()
        
        try:
            # Remove company from array in all customers that have it
            result = await collection.update_many(
                {
                    "company": {
                        "$elemMatch": {
                            "id": company_id
                        }
                    }
                },
                {
                    "$pull": {
                        "company": {"id": company_id}
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Cleared company reference from {result.modified_count} customer(s) for company ID: {company_id}")
            
            return result.modified_count
        except Exception as e:
            logger.error(f"Error clearing company reference: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
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
    
    @staticmethod
    async def update_license_type_by_company(company_id: ObjectId, new_license_type: str) -> int:
        """
        Updates the license type for all customers that belong to this company (active company only).
        Handles both old format (single object) and new format (array).
        Only updates customers with the company as active (isCompanyActive=True).
        
        Args:
            company_id: Company ObjectId
            new_license_type: New license type (Start or Hub)
            
        Returns:
            Number of customers updated
        """
        collection = CustomerRepository.get_collection()
        
        try:
            # Find all customers that have this company (both formats: array and single object)
            # Query for array format
            customers_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            # Query for single object format (backward compatibility)
            customers_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate by _id
            all_customers = {}
            for customer in customers_array:
                all_customers[str(customer["_id"])] = customer
            for customer in customers_single:
                all_customers[str(customer["_id"])] = customer
            
            updated_count = 0
            for customer_doc in all_customers.values():
                should_update = False
                
                if "company" in customer_doc:
                    # Handle array format
                    if isinstance(customer_doc["company"], list):
                        for company in customer_doc["company"]:
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
                    elif isinstance(customer_doc["company"], dict):
                        company_id_in_doc = customer_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Only update if the company is currently active
                                current_is_active = customer_doc["company"].get("isCompanyActive", True)
                                if current_is_active:
                                    should_update = True
                
                if should_update:
                    await collection.update_one(
                        {"_id": customer_doc["_id"]},
                        {
                            "$set": {
                                "license_type": new_license_type,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated license type to '{new_license_type}' for {updated_count} customer(s) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating license type by company: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise
    
    @staticmethod
    async def update_company_active_status(company_id: ObjectId, is_company_active: bool) -> int:
        """
        Updates the isCompanyActive field for all customers that belong to this company.
        Handles both old format (single object) and new format (array).
        
        Args:
            company_id: Company ObjectId
            is_company_active: New active status for the company
            
        Returns:
            Number of customers updated
        """
        collection = CustomerRepository.get_collection()
        
        try:
            # Find all customers that have this company (both formats: array and single object)
            # Query for array format
            customers_array = await collection.find({
                "company": {
                    "$elemMatch": {
                        "id": company_id
                    }
                }
            }).to_list(length=None)
            
            # Query for single object format (backward compatibility)
            customers_single = await collection.find({
                "company.id": company_id
            }).to_list(length=None)
            
            # Combine and deduplicate by _id
            all_customers = {}
            for customer in customers_array:
                all_customers[str(customer["_id"])] = customer
            for customer in customers_single:
                all_customers[str(customer["_id"])] = customer
            
            updated_count = 0
            for customer_doc in all_customers.values():
                updated = False
                
                if "company" in customer_doc:
                    # Handle array format
                    if isinstance(customer_doc["company"], list):
                        # Count how many companies are active
                        active_companies = [c for c in customer_doc["company"] if isinstance(c, dict) and c.get("isCompanyActive", True)]
                        has_multiple_companies = len(customer_doc["company"]) > 1
                        
                        for company in customer_doc["company"]:
                            if isinstance(company, dict):
                                company_id_in_doc = company.get("id")
                                # Compare ObjectId properly
                                if company_id_in_doc:
                                    company_matches = False
                                    if isinstance(company_id_in_doc, ObjectId):
                                        company_matches = (company_id_in_doc == company_id)
                                    elif str(company_id_in_doc) == str(company_id):
                                        company_matches = True
                                    
                                    if company_matches:
                                        # If customer has only one company (or this is the only active one), always update
                                        # If customer has multiple companies, only update the active one (preserve historical)
                                        current_is_active = company.get("isCompanyActive", True)
                                        if not has_multiple_companies or current_is_active:
                                            company["isCompanyActive"] = is_company_active
                                            updated = True
                    
                    # Handle single object format (backward compatibility)
                    # Always update single object format (it's the only company)
                    elif isinstance(customer_doc["company"], dict):
                        company_id_in_doc = customer_doc["company"].get("id")
                        if company_id_in_doc:
                            company_matches = False
                            if isinstance(company_id_in_doc, ObjectId):
                                company_matches = (company_id_in_doc == company_id)
                            elif str(company_id_in_doc) == str(company_id):
                                company_matches = True
                            
                            if company_matches:
                                # Single object format - always update (it's the only company)
                                customer_doc["company"]["isCompanyActive"] = is_company_active
                                updated = True
                
                if updated:
                    await collection.update_one(
                        {"_id": customer_doc["_id"]},
                        {
                            "$set": {
                                "company": customer_doc["company"],
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated isCompanyActive to {is_company_active} for {updated_count} customer(s) of company ID: {company_id}")
            
            return updated_count
        except Exception as e:
            logger.error(f"Error updating company active status: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)
            raise

