"""Routes for company management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.repositories.company_repository import CompanyRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.company_history_repository import CompanyHistoryRepository
from app.models.company import CompanyResponse, CompanyCreate, CompanyUpdate, CompanyPaginatedResponse
from app.models.company_history import CompanyHistoryCreate, CompanyHistoryResponse
from app.models.customer import CustomerResponse
from bson.errors import InvalidId
from bson import ObjectId
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(company: CompanyCreate):
    """Creates a new company."""
    try:
        company_created = await CompanyRepository.create(company)
        
        # Record creation in history
        try:
            await CompanyHistoryRepository.create(CompanyHistoryCreate(
                company_id=str(company_created.id),
                action="created",
                changes=None,
                user=None  # TODO: Get from authentication context
            ))
        except Exception as e:
            logger.warning(f"Failed to record creation history for company {company_created.id}: {e}")
        
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
            status=company_created.status,
            contract_expiration=company_created.contract_expiration,
            employee_count=company_created.employee_count,
            license_type=company_created.license_type,
            notes=company_created.notes,
            contract_renovated=company_created.contract_renovated,
            isActive=company_created.isActive,
            created_at=company_created.created_at,
            updated_at=company_created.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=CompanyPaginatedResponse)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    linked: Optional[bool] = Query(None, description="Filter by linked status"),
    license_type: Optional[str] = Query(None, pattern="^(Start|Hub)$", description="Filter by license type")
):
    """Lists companies with optional filters and pagination."""
    try:
        # Build filter dict for counting
        filter_dict = {}
        if active is not None:
            filter_dict["active"] = active
        if linked is not None:
            filter_dict["linked"] = linked
        if license_type:
            filter_dict["license_type"] = license_type
        
        # Get companies and total count
        companies = await CompanyRepository.list_by_filter(
            active=active,
            linked=linked,
            license_type=license_type,
            skip=skip,
            limit=limit
        )
        
        total = await CompanyRepository.count(filter_dict)
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return CompanyPaginatedResponse(
            data=[
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
                    status=c.status,
                    contract_expiration=c.contract_expiration,
                    employee_count=c.employee_count,
                    license_type=c.license_type,
                    notes=c.notes,
                    contract_renovated=c.contract_renovated,
                    isActive=c.isActive,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in companies
            ],
            total=total,
            page=page,
            limit=limit
        )
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
            status=company.status,
            contract_expiration=company.contract_expiration,
            employee_count=company.employee_count,
            license_type=company.license_type,
            notes=company.notes,
            contract_renovated=company.contract_renovated,
            isActive=company.isActive,
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
        # Get current company state before update
        current_company = await CompanyRepository.find_by_id(company_id)
        if not current_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Track changes for history
        update_dict = company_update.model_dump(exclude_unset=True)
        changes = {}
        
        # Compare old and new values to track changes
        for field, new_value in update_dict.items():
            old_value = getattr(current_company, field, None)
            if old_value != new_value:
                # Convert ObjectId and datetime to strings for JSON serialization
                old_str = str(old_value) if hasattr(old_value, '__str__') else old_value
                new_str = str(new_value) if hasattr(new_value, '__str__') else new_value
                changes[field] = {"old": old_str, "new": new_str}
        
        # Update company
        company = await CompanyRepository.update(company_id, company_update)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Record history if there are changes
        if changes:
            try:
                await CompanyHistoryRepository.create(CompanyHistoryCreate(
                    company_id=company_id,
                    action="updated",
                    changes=changes,
                    user=None  # TODO: Get from authentication context
                ))
            except Exception as e:
                logger.warning(f"Failed to record history for company {company_id}: {e}")
        
        # Check if company name was updated
        # If name changed, update it in all related customers
        if "name" in company_update.model_dump(exclude_unset=True):
            if current_company.name != company.name:
                logger.info(f"Company name changed from '{current_company.name}' to '{company.name}', updating customers")
                await CustomerRepository.update_company_name(company.id, company.name)
        
        # Check if license type was updated
        # If license_type changed, update it in all related customers
        if "license_type" in company_update.model_dump(exclude_unset=True):
            if current_company.license_type != company.license_type and company.license_type:
                logger.info(f"Company license type changed from '{current_company.license_type}' to '{company.license_type}', updating customers")
                await CustomerRepository.update_license_type_by_company(company.id, company.license_type)
        
        # Check if company was deactivated or unlinked
        # If active or linked changed to False, add contract record and set isActive
        active_changed = False
        linked_changed = False
        
        if "active" in company_update.model_dump(exclude_unset=True):
            if current_company.active != company.active:
                active_changed = True
                if not company.active:
                    logger.info(f"Company {company_id} was deactivated")
        
        if "linked" in company_update.model_dump(exclude_unset=True):
            if current_company.linked != company.linked:
                linked_changed = True
                if not company.linked:
                    logger.info(f"Company {company_id} was unlinked")
        
        # If company was deactivated or unlinked, add contract record
        if (active_changed and not company.active) or (linked_changed and not company.linked):
            # Set isActive to false
            await CompanyRepository.set_is_active(company_id, False)
            
            # Add contract renovation record
            # Using default values for age_contract and type_contract
            # These should ideally come from the company data or be passed as parameters
            age_contract = 0  # Default, should be calculated or provided
            type_contract = 1  # Default, should come from company data
            
            # Try to get from contract_expiration or other fields if available
            if company.contract_expiration:
                # Calculate age if contract_expiration exists
                from datetime import datetime
                if isinstance(company.contract_expiration, datetime):
                    delta = datetime.utcnow() - company.contract_expiration
                    age_contract = abs(delta.days)  # Age in days
            
            await CompanyRepository.add_contract_renovated(
                company_id=company_id,
                age_contract=age_contract,
                type_contract=type_contract,
                is_expirated=False  # Will be set to True below
            )
            
            # Mark the latest contract as expired
            await CompanyRepository.mark_latest_contract_expired(company_id)
            
            logger.info(f"Added contract renovation record for company {company_id} with isExpirated=true")
            
            # Reload company to get updated contract_renovated
            company = await CompanyRepository.find_by_id(company_id)
        
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
            status=company.status,
            contract_expiration=company.contract_expiration,
            employee_count=company.employee_count,
            license_type=company.license_type,
            notes=company.notes,
            contract_renovated=company.contract_renovated,
            isActive=company.isActive,
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


@router.get("/{company_id}/customers", response_model=List[CustomerResponse])
async def get_company_customers(
    company_id: str,
    active: Optional[bool] = Query(None, description="Filter by active status (true for active, false for inactive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    Lists all customers (employees) of a company.
    
    Args:
        company_id: Company ID
        active: Optional filter for active status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of customers associated with the company
    """
    try:
        # Verify company exists
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get customers by company
        customers = await CustomerRepository.list_by_company(
            company_id=company.id,
            active=active,
            skip=skip,
            limit=limit
        )
        
        return [CustomerResponse.from_customer(c) for c in customers]
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing company customers: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cnpj/{cnpj}", response_model=Dict[str, Any])
async def get_company_by_cnpj(cnpj: str):
    """
    Busca dados da empresa na ReceitaWS usando o CNPJ.
    
    Args:
        cnpj: CNPJ sem formatação (apenas números, 14 dígitos)
        
    Returns:
        Dict com os dados da empresa ou erro
    """
    try:
        # Remove formatação do CNPJ
        clean_cnpj = "".join(filter(str.isdigit, cnpj))
        
        if len(clean_cnpj) != 14:
            raise HTTPException(status_code=400, detail="CNPJ deve conter 14 dígitos")
        
        # Tenta múltiplas APIs de CNPJ
        apis = [
            f"https://www.receitaws.com.br/v1/{clean_cnpj}",
            f"https://brasilapi.com.br/api/cnpj/v1/{clean_cnpj}",
        ]
        
        for api_url in apis:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(api_url, headers={"Accept": "application/json"})
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Verifica se há erro na resposta
                        if data.get("status") == "ERROR" or data.get("message"):
                            continue  # Tenta próxima API
                        
                        # Normaliza os dados para formato padrão
                        normalized_data = {
                            "nome": data.get("nome") or data.get("razao_social") or data.get("name"),
                            "fantasia": data.get("fantasia") or data.get("nome_fantasia"),
                            "email": data.get("email"),
                            "telefone": data.get("telefone") or (f"{data.get('ddd', '')}{data.get('telefone1', '')}" if data.get("ddd") and data.get("telefone1") else None),
                            "logradouro": data.get("logradouro") or (data.get("endereco", {}).get("logradouro") if isinstance(data.get("endereco"), dict) else None),
                            "numero": data.get("numero") or (data.get("endereco", {}).get("numero") if isinstance(data.get("endereco"), dict) else None),
                            "complemento": data.get("complemento") or (data.get("endereco", {}).get("complemento") if isinstance(data.get("endereco"), dict) else None),
                            "bairro": data.get("bairro") or (data.get("endereco", {}).get("bairro") if isinstance(data.get("endereco"), dict) else None),
                            "municipio": data.get("municipio") or (data.get("endereco", {}).get("municipio") if isinstance(data.get("endereco"), dict) else None) or data.get("cidade"),
                            "uf": data.get("uf") or (data.get("endereco", {}).get("uf") if isinstance(data.get("endereco"), dict) else None) or data.get("estado"),
                            "cep": data.get("cep") or (data.get("endereco", {}).get("cep") if isinstance(data.get("endereco"), dict) else None),
                        }
                        
                        # Remove campos None
                        normalized_data = {k: v for k, v in normalized_data.items() if v is not None}
                        
                        logger.info(f"Company data fetched successfully for CNPJ: {clean_cnpj}")
                        return normalized_data
                        
            except httpx.RequestError as e:
                logger.warning(f"Error fetching from {api_url}: {str(e)}")
                continue  # Tenta próxima API
            except Exception as e:
                logger.warning(f"Unexpected error from {api_url}: {str(e)}")
                continue
        
        # Se nenhuma API funcionou
        raise HTTPException(
            status_code=404, 
            detail="Não foi possível encontrar dados para este CNPJ. Verifique se o CNPJ está correto."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company by CNPJ: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados do CNPJ: {str(e)}")


@router.get("/{company_id}/history", response_model=List[CompanyHistoryResponse])
async def get_company_history(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Gets the change history for a company."""
    try:
        # Verify company exists
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get history
        history = await CompanyHistoryRepository.list_by_company(company_id, skip=skip, limit=limit)
        
        return [
            CompanyHistoryResponse(
                id=str(h.id),
                company_id=str(h.company_id),
                action=h.action,
                changes=h.changes,
                user=h.user,
                timestamp=h.timestamp,
                created_at=h.created_at
            )
            for h in history
        ]
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company history: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: str):
    """Deletes a company."""
    try:
        # Get company before deletion to clear customer references
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Clear customer references before deleting
        await CustomerRepository.clear_company_reference(company.id)
        
        # Record deletion in history before deleting
        try:
            await CompanyHistoryRepository.create(CompanyHistoryCreate(
                company_id=company_id,
                action="deleted",
                changes=None,
                user=None  # TODO: Get from authentication context
            ))
        except Exception as e:
            logger.warning(f"Failed to record deletion history for company {company_id}: {e}")
        
        # Delete company
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

