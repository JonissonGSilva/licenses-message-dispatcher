"""Routes for team management (Direta, Indicador, Parceiro, Negocio)."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.repositories.team_repository import (
    DiretaRepository, IndicadorRepository, ParceiroRepository, NegocioRepository
)
from app.models.team import (
    DiretaResponse, DiretaCreate, DiretaUpdate, DiretaPaginatedResponse,
    IndicadorResponse, IndicadorCreate, IndicadorUpdate, IndicadorPaginatedResponse,
    ParceiroResponse, ParceiroCreate, ParceiroUpdate, ParceiroPaginatedResponse,
    ParceiroWithNegociosResponse, NegocioResponse, NegocioCreate, NegocioUpdate
)
from app.models.customer import normalize_company_field, normalize_company_array_field, normalize_company_array_field_for_response
from bson.errors import InvalidId
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/equipes", tags=["Equipes"])


# ==================== DIRETA ====================

@router.post("/direta", response_model=DiretaResponse, status_code=201)
async def create_direta(direta: DiretaCreate):
    """Creates a new Direta member."""
    try:
        direta_created = await DiretaRepository.create(direta)
        return DiretaResponse(
            id=str(direta_created.id),
            name=direta_created.name,
            cpf=direta_created.cpf,
            phone=direta_created.phone,
            email=direta_created.email,
            type=direta_created.type,
            function=direta_created.function,
            remuneration=direta_created.remuneration,
            commission=direta_created.commission,
            created_at=direta_created.created_at,
            updated_at=direta_created.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating direta: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/direta", response_model=DiretaPaginatedResponse)
async def list_direta(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lists Direta members with pagination."""
    try:
        direta_list = await DiretaRepository.list_all(skip=skip, limit=limit)
        total = await DiretaRepository.count()
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return DiretaPaginatedResponse(
            data=[
                DiretaResponse(
                    id=str(d.id),
                    name=d.name,
                    cpf=d.cpf,
                    phone=d.phone,
                    email=d.email,
                    type=d.type,
                    function=d.function,
                    remuneration=d.remuneration,
                    commission=d.commission,
                    created_at=d.created_at,
                    updated_at=d.updated_at
                )
                for d in direta_list
            ],
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing direta: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/direta/{direta_id}", response_model=DiretaResponse)
async def get_direta(direta_id: str):
    """Gets a Direta member by ID."""
    try:
        direta = await DiretaRepository.get_by_id(direta_id)
        if not direta:
            raise HTTPException(status_code=404, detail="Direta member not found")
        
        return DiretaResponse(
            id=str(direta.id),
            name=direta.name,
            cpf=direta.cpf,
            phone=direta.phone,
            email=direta.email,
            type=direta.type,
            function=direta.function,
            remuneration=direta.remuneration,
            commission=direta.commission,
            created_at=direta.created_at,
            updated_at=direta.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting direta: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/direta/{direta_id}", response_model=DiretaResponse)
async def update_direta(direta_id: str, direta_update: DiretaUpdate):
    """Updates a Direta member."""
    try:
        direta = await DiretaRepository.update(direta_id, direta_update)
        if not direta:
            raise HTTPException(status_code=404, detail="Direta member not found")
        
        return DiretaResponse(
            id=str(direta.id),
            name=direta.name,
            cpf=direta.cpf,
            phone=direta.phone,
            email=direta.email,
            type=direta.type,
            function=direta.function,
            remuneration=direta.remuneration,
            commission=direta.commission,
            created_at=direta.created_at,
            updated_at=direta.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating direta: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/direta/{direta_id}", status_code=204)
async def delete_direta(direta_id: str):
    """Deletes a Direta member."""
    try:
        deleted = await DiretaRepository.delete(direta_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Direta member not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting direta: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INDICADOR ====================

@router.post("/indicador", response_model=IndicadorResponse, status_code=201)
async def create_indicador(indicador: IndicadorCreate):
    """Creates a new Indicador."""
    try:
        # Validate company if provided
        if indicador.company and isinstance(indicador.company, str):
            from app.repositories.team_repository import TeamRepository
            company_ref = await TeamRepository.resolve_company_reference(indicador.company, validate_status=True)
            if not company_ref:
                raise HTTPException(
                    status_code=400,
                    detail=f"Company '{indicador.company}' not found or is not active"
                )
        
        indicador_created = await IndicadorRepository.create(indicador)
        
        return IndicadorResponse(
            id=str(indicador_created.id),
            name=indicador_created.name,
            company=normalize_company_array_field_for_response(indicador_created.company),
            phone=indicador_created.phone,
            email=indicador_created.email,
            commission=indicador_created.commission,
            created_at=indicador_created.created_at,
            updated_at=indicador_created.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicador", response_model=IndicadorPaginatedResponse)
async def list_indicador(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lists Indicadores with pagination."""
    try:
        indicador_list = await IndicadorRepository.list_all(skip=skip, limit=limit)
        total = await IndicadorRepository.count()
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return IndicadorPaginatedResponse(
            data=[
                IndicadorResponse(
                    id=str(i.id),
                    name=i.name,
                    company=normalize_company_array_field_for_response(i.company),
                    phone=i.phone,
                    email=i.email,
                    commission=i.commission,
                    created_at=i.created_at,
                    updated_at=i.updated_at
                )
                for i in indicador_list
            ],
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicador/{indicador_id}", response_model=IndicadorResponse)
async def get_indicador(indicador_id: str):
    """Gets an Indicador by ID."""
    try:
        indicador = await IndicadorRepository.get_by_id(indicador_id)
        if not indicador:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
        
        return IndicadorResponse(
            id=str(indicador.id),
            name=indicador.name,
            company=normalize_company_array_field_for_response(indicador.company),
            phone=indicador.phone,
            email=indicador.email,
            commission=indicador.commission,
            created_at=indicador.created_at,
            updated_at=indicador.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/indicador/{indicador_id}", response_model=IndicadorResponse)
async def update_indicador(indicador_id: str, indicador_update: IndicadorUpdate):
    """Updates an Indicador."""
    try:
        # Validate company if provided
        if "company" in indicador_update.model_dump(exclude_unset=True):
            company_value = indicador_update.company
            if company_value and isinstance(company_value, str):
                from app.repositories.team_repository import TeamRepository
                company_ref = await TeamRepository.resolve_company_reference(company_value, validate_status=True)
                if not company_ref:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Company '{company_value}' not found or is not active"
                    )
        
        indicador = await IndicadorRepository.update(indicador_id, indicador_update)
        if not indicador:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
        
        return IndicadorResponse(
            id=str(indicador.id),
            name=indicador.name,
            company=normalize_company_array_field_for_response(indicador.company),
            phone=indicador.phone,
            email=indicador.email,
            commission=indicador.commission,
            created_at=indicador.created_at,
            updated_at=indicador.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/indicador/{indicador_id}", status_code=204)
async def delete_indicador(indicador_id: str):
    """Deletes an Indicador."""
    try:
        deleted = await IndicadorRepository.delete(indicador_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Request schema for linking companies
class LinkCompanyRequest(BaseModel):
    """Request schema for linking a company."""
    company_name: str = Field(..., min_length=1, description="Company name to link")


@router.post("/indicador/{indicador_id}/link-company", response_model=IndicadorResponse)
async def link_company_to_indicador(indicador_id: str, request: LinkCompanyRequest):
    """Links a company to an Indicador. Validates that the company is not already linked."""
    try:
        indicador = await IndicadorRepository.link_company(indicador_id, request.company_name)
        if not indicador:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
        
        logger.info(f"Company '{request.company_name}' linked to indicador '{indicador.name}' (ID: {indicador_id})")
        
        return IndicadorResponse(
            id=str(indicador.id),
            name=indicador.name,
            company=normalize_company_array_field_for_response(indicador.company),
            phone=indicador.phone,
            email=indicador.email,
            commission=indicador.commission,
            created_at=indicador.created_at,
            updated_at=indicador.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking company to indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/indicador/{indicador_id}/unlink-company", response_model=IndicadorResponse)
async def unlink_company_from_indicador(indicador_id: str):
    """Unlinks the active company from an Indicador."""
    try:
        indicador = await IndicadorRepository.unlink_company(indicador_id)
        if not indicador:
            raise HTTPException(status_code=404, detail="Indicador não encontrado")
        
        logger.info(f"Company unlinked from indicador '{indicador.name}' (ID: {indicador_id})")
        
        return IndicadorResponse(
            id=str(indicador.id),
            name=indicador.name,
            company=normalize_company_array_field_for_response(indicador.company),
            phone=indicador.phone,
            email=indicador.email,
            commission=indicador.commission,
            created_at=indicador.created_at,
            updated_at=indicador.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking company from indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PARCEIRO ====================

@router.post("/parceiro", response_model=ParceiroResponse, status_code=201)
async def create_parceiro(parceiro: ParceiroCreate):
    """Creates a new Parceiro."""
    try:
        # Validate company if provided
        if parceiro.company and isinstance(parceiro.company, str):
            from app.repositories.team_repository import TeamRepository
            company_ref = await TeamRepository.resolve_company_reference(parceiro.company, validate_status=True)
            if not company_ref:
                raise HTTPException(
                    status_code=400,
                    detail=f"Company '{parceiro.company}' not found or is not active"
                )
        
        parceiro_created = await ParceiroRepository.create(parceiro)
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(str(parceiro_created.id))
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro_created.id),
            name=parceiro_created.name,
            company=normalize_company_array_field_for_response(parceiro_created.company),
            type=parceiro_created.type,
            phone=parceiro_created.phone,
            email=parceiro_created.email,
            commission=parceiro_created.commission,
            created_at=parceiro_created.created_at,
            updated_at=parceiro_created.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    third_party_company=n.third_party_company,
                    type=n.type,
                    license_count=n.license_count,
                    negotiation_value=n.negotiation_value,
                    contract_duration=n.contract_duration,
                    start_date=n.start_date,
                    payment_date=n.payment_date,
                    created_at=n.created_at,
                    updated_at=n.updated_at
                )
                for n in negocios
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parceiro", response_model=ParceiroPaginatedResponse)
async def list_parceiro(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lists Parceiros with pagination."""
    try:
        parceiro_list = await ParceiroRepository.list_all(skip=skip, limit=limit)
        total = await ParceiroRepository.count()
        page = (skip // limit) + 1 if limit > 0 else 1
        
        # Get negocios for each parceiro
        parceiros_with_negocios = []
        for parceiro in parceiro_list:
            negocios = await NegocioRepository.list_by_parceiro(str(parceiro.id))
            parceiros_with_negocios.append(
                ParceiroWithNegociosResponse(
                    id=str(parceiro.id),
                    name=parceiro.name,
                    company=normalize_company_array_field_for_response(parceiro.company),
                    type=parceiro.type,
                    phone=parceiro.phone,
                    email=parceiro.email,
                    commission=parceiro.commission,
                    created_at=parceiro.created_at,
                    updated_at=parceiro.updated_at,
                    negocios=[
                        NegocioResponse(
                            id=str(n.id),
                            third_party_company=n.third_party_company,
                            type=n.type,
                            license_count=n.license_count,
                            negotiation_value=n.negotiation_value,
                            contract_duration=n.contract_duration,
                            start_date=n.start_date,
                            payment_date=n.payment_date,
                            created_at=n.created_at,
                            updated_at=n.updated_at
                        )
                        for n in negocios
                    ]
                )
            )
        
        return ParceiroPaginatedResponse(
            data=parceiros_with_negocios,
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parceiro/{parceiro_id}", response_model=ParceiroWithNegociosResponse)
async def get_parceiro(parceiro_id: str):
    """Gets a Parceiro by ID."""
    try:
        parceiro = await ParceiroRepository.get_by_id(parceiro_id)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            name=parceiro.name,
            company=normalize_company_array_field_for_response(parceiro.company),
            type=parceiro.type,
            phone=parceiro.phone,
            email=parceiro.email,
            commission=parceiro.commission,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    third_party_company=n.third_party_company,
                    type=n.type,
                    license_count=n.license_count,
                    negotiation_value=n.negotiation_value,
                    contract_duration=n.contract_duration,
                    start_date=n.start_date,
                    payment_date=n.payment_date,
                    created_at=n.created_at,
                    updated_at=n.updated_at
                )
                for n in negocios
            ]
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/parceiro/{parceiro_id}", response_model=ParceiroWithNegociosResponse)
async def update_parceiro(parceiro_id: str, parceiro_update: ParceiroUpdate):
    """Updates a Parceiro."""
    try:
        # Validate company if provided
        if "company" in parceiro_update.model_dump(exclude_unset=True):
            company_value = parceiro_update.company
            if company_value and isinstance(company_value, str):
                from app.repositories.team_repository import TeamRepository
                company_ref = await TeamRepository.resolve_company_reference(company_value, validate_status=True)
                if not company_ref:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Company '{company_value}' not found or is not active"
                    )
        
        parceiro = await ParceiroRepository.update(parceiro_id, parceiro_update)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            name=parceiro.name,
            company=normalize_company_array_field_for_response(parceiro.company),
            type=parceiro.type,
            phone=parceiro.phone,
            email=parceiro.email,
            commission=parceiro.commission,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    third_party_company=n.third_party_company,
                    type=n.type,
                    license_count=n.license_count,
                    negotiation_value=n.negotiation_value,
                    contract_duration=n.contract_duration,
                    start_date=n.start_date,
                    payment_date=n.payment_date,
                    created_at=n.created_at,
                    updated_at=n.updated_at
                )
                for n in negocios
            ]
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/parceiro/{parceiro_id}", status_code=204)
async def delete_parceiro(parceiro_id: str):
    """Deletes a Parceiro."""
    try:
        deleted = await ParceiroRepository.delete(parceiro_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parceiro/{parceiro_id}/link-company", response_model=ParceiroWithNegociosResponse)
async def link_company_to_parceiro(parceiro_id: str, request: LinkCompanyRequest):
    """Links a company to a Parceiro. Validates that the company is not already linked."""
    try:
        parceiro = await ParceiroRepository.link_company(parceiro_id, request.company_name)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            name=parceiro.name,
            company=normalize_company_array_field_for_response(parceiro.company),
            type=parceiro.type,
            phone=parceiro.phone,
            email=parceiro.email,
            commission=parceiro.commission,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    third_party_company=n.third_party_company,
                    type=n.type,
                    license_count=n.license_count,
                    negotiation_value=n.negotiation_value,
                    contract_duration=n.contract_duration,
                    start_date=n.start_date,
                    payment_date=n.payment_date,
                    created_at=n.created_at,
                    updated_at=n.updated_at
                )
                for n in negocios
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking company to parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/parceiro/{parceiro_id}/unlink-company", response_model=ParceiroWithNegociosResponse)
async def unlink_company_from_parceiro(parceiro_id: str):
    """Unlinks the active company from a Parceiro."""
    try:
        parceiro = await ParceiroRepository.unlink_company(parceiro_id)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        logger.info(f"Company unlinked from parceiro '{parceiro.name}' (ID: {parceiro_id})")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            name=parceiro.name,
            company=normalize_company_array_field_for_response(parceiro.company),
            type=parceiro.type,
            phone=parceiro.phone,
            email=parceiro.email,
            commission=parceiro.commission,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    third_party_company=n.third_party_company,
                    type=n.type,
                    license_count=n.license_count,
                    negotiation_value=n.negotiation_value,
                    contract_duration=n.contract_duration,
                    start_date=n.start_date,
                    payment_date=n.payment_date,
                    created_at=n.created_at,
                    updated_at=n.updated_at
                )
                for n in negocios
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking company from parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEGOCIO ====================

@router.post("/parceiro/{parceiro_id}/negocio", response_model=NegocioResponse, status_code=201)
async def create_negocio(parceiro_id: str, negocio: NegocioCreate):
    """Creates a new Negocio for a Parceiro."""
    try:
        # Verify parceiro exists
        parceiro = await ParceiroRepository.get_by_id(parceiro_id)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        negocio_created = await NegocioRepository.create(negocio, parceiro_id)
        
        return NegocioResponse(
            id=str(negocio_created.id),
            third_party_company=negocio_created.third_party_company,
            type=negocio_created.type,
            license_count=negocio_created.license_count,
            negotiation_value=negocio_created.negotiation_value,
            contract_duration=negocio_created.contract_duration,
            start_date=negocio_created.start_date,
            payment_date=negocio_created.payment_date,
            created_at=negocio_created.created_at,
            updated_at=negocio_created.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating negocio: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parceiro/{parceiro_id}/negocio", response_model=List[NegocioResponse])
async def list_negocios(parceiro_id: str):
    """Lists all Negocios for a Parceiro."""
    try:
        # Verify parceiro exists
        parceiro = await ParceiroRepository.get_by_id(parceiro_id)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro não encontrado")
        
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return [
            NegocioResponse(
                id=str(n.id),
                third_party_company=n.third_party_company,
                type=n.type,
                license_count=n.license_count,
                negotiation_value=n.negotiation_value,
                contract_duration=n.contract_duration,
                start_date=n.start_date,
                payment_date=n.payment_date,
                created_at=n.created_at,
                updated_at=n.updated_at
            )
            for n in negocios
        ]
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing negocios: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/negocio/{negocio_id}", response_model=NegocioResponse)
async def get_negocio(negocio_id: str):
    """Gets a Negocio by ID."""
    try:
        negocio = await NegocioRepository.get_by_id(negocio_id)
        if not negocio:
            raise HTTPException(status_code=404, detail="Negocio not found")
        
        return NegocioResponse(
            id=str(negocio.id),
            third_party_company=negocio.third_party_company,
            type=negocio.type,
            license_count=negocio.license_count,
            negotiation_value=negocio.negotiation_value,
            contract_duration=negocio.contract_duration,
            start_date=negocio.start_date,
            payment_date=negocio.payment_date,
            created_at=negocio.created_at,
            updated_at=negocio.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting negocio: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/negocio/{negocio_id}", response_model=NegocioResponse)
async def update_negocio(negocio_id: str, negocio_update: NegocioUpdate):
    """Updates a Negocio."""
    try:
        negocio = await NegocioRepository.update(negocio_id, negocio_update)
        if not negocio:
            raise HTTPException(status_code=404, detail="Negocio not found")
        
        return NegocioResponse(
            id=str(negocio.id),
            third_party_company=negocio.third_party_company,
            type=negocio.type,
            license_count=negocio.license_count,
            negotiation_value=negocio.negotiation_value,
            contract_duration=negocio.contract_duration,
            start_date=negocio.start_date,
            payment_date=negocio.payment_date,
            created_at=negocio.created_at,
            updated_at=negocio.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating negocio: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/negocio/{negocio_id}", status_code=204)
async def delete_negocio(negocio_id: str):
    """Deletes a Negocio."""
    try:
        deleted = await NegocioRepository.delete(negocio_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Negocio not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting negocio: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

