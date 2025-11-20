"""Routes for license management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.repositories.license_repository import LicenseRepository
from app.models.license import LicenseResponse, LicenseCreate, LicenseUpdate
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/licenses", tags=["Licenses"])


@router.post("", response_model=LicenseResponse, status_code=201)
async def create_license(license: LicenseCreate):
    """Creates a new license."""
    try:
        license_created = await LicenseRepository.create(license)
        return LicenseResponse(
            id=str(license_created.id),
            customer_id=str(license_created.customer_id),
            license_type=license_created.license_type,
            status=license_created.status,
            portal_id=license_created.portal_id,
            created_at=license_created.created_at,
            updated_at=license_created.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating license: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[LicenseResponse])
async def list_licenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lists all licenses."""
    try:
        licenses = await LicenseRepository.list_all(skip=skip, limit=limit)
        
        return [
            LicenseResponse(
                id=str(l.id),
                customer_id=str(l.customer_id),
                license_type=l.license_type,
                status=l.status,
                portal_id=l.portal_id,
                created_at=l.created_at,
                updated_at=l.updated_at
            )
            for l in licenses
        ]
    except Exception as e:
        logger.error(f"Error listing licenses: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{license_id}", response_model=LicenseResponse)
async def get_license(license_id: str):
    """Gets a license by ID."""
    try:
        license = await LicenseRepository.find_by_id(license_id)
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        
        return LicenseResponse(
            id=str(license.id),
            customer_id=str(license.customer_id),
            license_type=license.license_type,
            status=license.status,
            portal_id=license.portal_id,
            created_at=license.created_at,
            updated_at=license.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting license: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{license_id}", response_model=LicenseResponse)
async def update_license(license_id: str, license_update: LicenseUpdate):
    """Updates a license."""
    try:
        license = await LicenseRepository.update(license_id, license_update)
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        
        return LicenseResponse(
            id=str(license.id),
            customer_id=str(license.customer_id),
            license_type=license.license_type,
            status=license.status,
            portal_id=license.portal_id,
            created_at=license.created_at,
            updated_at=license.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating license: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

