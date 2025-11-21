"""Routes for company management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.repositories.company_repository import CompanyRepository
from app.models.company import CompanyResponse, CompanyCreate, CompanyUpdate
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(company: CompanyCreate):
    """Creates a new company."""
    try:
        company_created = await CompanyRepository.create(company)
        return CompanyResponse(
            id=str(company_created.id),
            name=company_created.name,
            cnpj=company_created.cnpj,
            email=company_created.email,
            phone=company_created.phone,
            address=company_created.address,
            city=company_created.city,
            state=company_created.state,
            zip_code=company_created.zip_code,
            linked=company_created.linked,
            active=company_created.active,
            license_timeout=company_created.license_timeout,
            contract_expiration=company_created.contract_expiration,
            employee_count=company_created.employee_count,
            license_type=company_created.license_type,
            portal_id=company_created.portal_id,
            notes=company_created.notes,
            created_at=company_created.created_at,
            updated_at=company_created.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    linked: Optional[bool] = Query(None, description="Filter by linked status"),
    license_type: Optional[str] = Query(None, pattern="^(Start|Hub)$", description="Filter by license type")
):
    """Lists companies with optional filters."""
    try:
        companies = await CompanyRepository.list_by_filter(
            active=active,
            linked=linked,
            license_type=license_type,
            skip=skip,
            limit=limit
        )
        
        return [
            CompanyResponse(
                id=str(c.id),
                name=c.name,
                cnpj=c.cnpj,
                email=c.email,
                phone=c.phone,
                address=c.address,
                city=c.city,
                state=c.state,
                zip_code=c.zip_code,
                linked=c.linked,
                active=c.active,
                license_timeout=c.license_timeout,
                contract_expiration=c.contract_expiration,
                employee_count=c.employee_count,
                license_type=c.license_type,
                portal_id=c.portal_id,
                notes=c.notes,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in companies
        ]
    except Exception as e:
        logger.error(f"Error listing companies: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """Gets a company by ID."""
    try:
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(
            id=str(company.id),
            name=company.name,
            cnpj=company.cnpj,
            email=company.email,
            phone=company.phone,
            address=company.address,
            city=company.city,
            state=company.state,
            zip_code=company.zip_code,
            linked=company.linked,
            active=company.active,
            license_timeout=company.license_timeout,
            contract_expiration=company.contract_expiration,
            employee_count=company.employee_count,
            license_type=company.license_type,
            portal_id=company.portal_id,
            notes=company.notes,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: str, company_update: CompanyUpdate):
    """Updates a company."""
    try:
        company = await CompanyRepository.update(company_id, company_update)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(
            id=str(company.id),
            name=company.name,
            cnpj=company.cnpj,
            email=company.email,
            phone=company.phone,
            address=company.address,
            city=company.city,
            state=company.state,
            zip_code=company.zip_code,
            linked=company.linked,
            active=company.active,
            license_timeout=company.license_timeout,
            contract_expiration=company.contract_expiration,
            employee_count=company.employee_count,
            license_type=company.license_type,
            portal_id=company.portal_id,
            notes=company.notes,
            created_at=company.created_at,
            updated_at=company.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: str):
    """Deletes a company."""
    try:
        deleted = await CompanyRepository.delete(company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Company not found")
        return None
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

