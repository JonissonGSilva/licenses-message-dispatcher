"""Routes for customer management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.repositories.customer_repository import CustomerRepository
from app.repositories.company_repository import CompanyRepository
from app.models.customer import CustomerResponse, CustomerCreate, CustomerUpdate, AssociateCompanyRequest
from bson.errors import InvalidId
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(customer: CustomerCreate):
    """Creates a new customer."""
    try:
        # Validate company if provided (must exist, be linked and active)
        if customer.company and isinstance(customer.company, str):
            company_ref = await CustomerRepository.resolve_company_reference(customer.company, validate_status=True)
            if not company_ref:
                raise HTTPException(
                    status_code=400,
                    detail=f"Company '{customer.company}' not found, is not linked, or is not active. Company must exist in Companies collection with linked=true and active=true"
                )
        
        customer_created = await CustomerRepository.create(customer)
        return CustomerResponse.from_customer(customer_created)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    license_type: Optional[str] = Query(None, pattern="^(Start|Hub)$"),
    active: Optional[bool] = Query(None)
):
    """Lists customers with optional filters."""
    try:
        if license_type:
            customers = await CustomerRepository.list_by_license_type(license_type, active)
        else:
            customers = await CustomerRepository.list_all(skip=skip, limit=limit)
        
        return [CustomerResponse.from_customer(c) for c in customers]
    except Exception as e:
        logger.error(f"Error listing customers: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    """Gets a customer by ID."""
    try:
        customer = await CustomerRepository.find_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse.from_customer(customer)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """Updates a customer."""
    try:
        # Validate company if provided (must exist, be linked and active)
        if "company" in customer_update.model_dump(exclude_unset=True):
            company_value = customer_update.company
            if company_value and isinstance(company_value, str):
                company_ref = await CustomerRepository.resolve_company_reference(company_value, validate_status=True)
                if not company_ref:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Company '{company_value}' not found, is not linked, or is not active. Company must exist in Companies collection with linked=true and active=true"
                    )
        
        customer = await CustomerRepository.update(customer_id, customer_update)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse.from_customer(customer)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{customer_id}/associate-company", response_model=CustomerResponse)
async def associate_company_to_customer(
    customer_id: str,
    request: AssociateCompanyRequest
):
    """
    Associates a company to a customer.
    
    You can provide either company_id or company_name.
    The company must exist, be linked=true and active=true.
    
    Args:
        customer_id: Customer ID
        request: Request body with company_id or company_name
        
    Returns:
        Updated customer with company reference
    """
    try:
        # Verify customer exists
        customer = await CustomerRepository.find_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Validate that at least one identifier is provided
        if not request.company_id and not request.company_name:
            raise HTTPException(
                status_code=400,
                detail="Either company_id or company_name must be provided"
            )
        
        # Find company by ID or name
        company = None
        if request.company_id:
            try:
                company = await CompanyRepository.find_by_id(request.company_id)
                if not company:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Company with ID '{request.company_id}' not found"
                    )
            except InvalidId:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid company ID format: '{request.company_id}'"
                )
        elif request.company_name:
            company = await CompanyRepository.find_by_name(request.company_name)
            if not company:
                raise HTTPException(
                    status_code=404,
                    detail=f"Company with name '{request.company_name}' not found"
                )
        
        # Validate company status (must be linked and active)
        if not company.linked or not company.active:
            raise HTTPException(
                status_code=400,
                detail=f"Company '{company.name}' is not valid for association. Company must have linked=true and active=true. Current status: linked={company.linked}, active={company.active}"
            )
        
        # Update customer with company reference
        customer_update = CustomerUpdate(company=company.name)
        updated_customer = await CustomerRepository.update(customer_id, customer_update)
        
        if not updated_customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        logger.info(f"Company '{company.name}' (ID: {company.id}) associated to customer '{updated_customer.name}' (ID: {customer_id})")
        
        return CustomerResponse.from_customer(updated_customer)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating company to customer: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: str):
    """Deletes a customer."""
    try:
        deleted = await CustomerRepository.delete(customer_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Customer not found")
        return None
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

