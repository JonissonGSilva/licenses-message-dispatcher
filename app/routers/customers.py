"""Routes for customer management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.repositories.customer_repository import CustomerRepository
from app.models.customer import CustomerResponse, CustomerCreate, CustomerUpdate
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(customer: CustomerCreate):
    """Creates a new customer."""
    try:
        customer_created = await CustomerRepository.create(customer)
        return CustomerResponse.from_customer(customer_created)
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

