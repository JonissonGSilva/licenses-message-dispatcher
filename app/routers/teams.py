"""Routes for team management (Direta, Indicador, Parceiro, Negocio)."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.repositories.team_repository import (
    DiretaRepository, IndicadorRepository, ParceiroRepository, NegocioRepository
)
from app.models.team import (
    DiretaResponse, DiretaCreate, DiretaUpdate, DiretaPaginatedResponse,
    IndicadorResponse, IndicadorCreate, IndicadorUpdate, IndicadorPaginatedResponse,
    ParceiroResponse, ParceiroCreate, ParceiroUpdate, ParceiroPaginatedResponse,
    ParceiroWithNegociosResponse, NegocioResponse, NegocioCreate, NegocioUpdate
)
from app.models.customer import normalize_company_field
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
            nome=direta_created.nome,
            cpf=direta_created.cpf,
            telefone=direta_created.telefone,
            email=direta_created.email,
            tipo=direta_created.tipo,
            funcao=direta_created.funcao,
            remuneracao=direta_created.remuneracao,
            comissao=direta_created.comissao,
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
                    nome=d.nome,
                    cpf=d.cpf,
                    telefone=d.telefone,
                    email=d.email,
                    tipo=d.tipo,
                    funcao=d.funcao,
                    remuneracao=d.remuneracao,
                    comissao=d.comissao,
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
            nome=direta.nome,
            cpf=direta.cpf,
            telefone=direta.telefone,
            email=direta.email,
            tipo=direta.tipo,
            funcao=direta.funcao,
            remuneracao=direta.remuneracao,
            comissao=direta.comissao,
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
            nome=direta.nome,
            cpf=direta.cpf,
            telefone=direta.telefone,
            email=direta.email,
            tipo=direta.tipo,
            funcao=direta.funcao,
            remuneracao=direta.remuneracao,
            comissao=direta.comissao,
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
        if indicador.empresa and isinstance(indicador.empresa, str):
            from app.repositories.team_repository import TeamRepository
            company_ref = await TeamRepository.resolve_company_reference(indicador.empresa, validate_status=True)
            if not company_ref:
                raise HTTPException(
                    status_code=400,
                    detail=f"Company '{indicador.empresa}' not found, is not linked, or is not active"
                )
        
        indicador_created = await IndicadorRepository.create(indicador)
        
        return IndicadorResponse(
            id=str(indicador_created.id),
            nome=indicador_created.nome,
            empresa=normalize_company_field(indicador_created.empresa),
            telefone=indicador_created.telefone,
            email=indicador_created.email,
            comissao=indicador_created.comissao,
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
                    nome=i.nome,
                    empresa=normalize_company_field(i.empresa),
                    telefone=i.telefone,
                    email=i.email,
                    comissao=i.comissao,
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
            raise HTTPException(status_code=404, detail="Indicador not found")
        
        return IndicadorResponse(
            id=str(indicador.id),
            nome=indicador.nome,
            empresa=normalize_company_field(indicador.empresa),
            telefone=indicador.telefone,
            email=indicador.email,
            comissao=indicador.comissao,
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
        if "empresa" in indicador_update.model_dump(exclude_unset=True):
            company_value = indicador_update.empresa
            if company_value and isinstance(company_value, str):
                from app.repositories.team_repository import TeamRepository
                company_ref = await TeamRepository.resolve_company_reference(company_value, validate_status=True)
                if not company_ref:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Company '{company_value}' not found, is not linked, or is not active"
                    )
        
        indicador = await IndicadorRepository.update(indicador_id, indicador_update)
        if not indicador:
            raise HTTPException(status_code=404, detail="Indicador not found")
        
        return IndicadorResponse(
            id=str(indicador.id),
            nome=indicador.nome,
            empresa=normalize_company_field(indicador.empresa),
            telefone=indicador.telefone,
            email=indicador.email,
            comissao=indicador.comissao,
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
            raise HTTPException(status_code=404, detail="Indicador not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting indicador: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PARCEIRO ====================

@router.post("/parceiro", response_model=ParceiroResponse, status_code=201)
async def create_parceiro(parceiro: ParceiroCreate):
    """Creates a new Parceiro."""
    try:
        # Validate company if provided
        if parceiro.empresa and isinstance(parceiro.empresa, str):
            from app.repositories.team_repository import TeamRepository
            company_ref = await TeamRepository.resolve_company_reference(parceiro.empresa, validate_status=True)
            if not company_ref:
                raise HTTPException(
                    status_code=400,
                    detail=f"Company '{parceiro.empresa}' not found, is not linked, or is not active"
                )
        
        parceiro_created = await ParceiroRepository.create(parceiro)
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(str(parceiro_created.id))
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro_created.id),
            nome=parceiro_created.nome,
            empresa=normalize_company_field(parceiro_created.empresa),
            tipo=parceiro_created.tipo,
            telefone=parceiro_created.telefone,
            email=parceiro_created.email,
            comissao=parceiro_created.comissao,
            created_at=parceiro_created.created_at,
            updated_at=parceiro_created.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    empresa_terceira=n.empresa_terceira,
                    tipo=n.tipo,
                    qtd_licencas=n.qtd_licencas,
                    valor_negociacao=n.valor_negociacao,
                    tempo_contrato=n.tempo_contrato,
                    data_inicio=n.data_inicio,
                    data_pagamento=n.data_pagamento,
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
                    nome=parceiro.nome,
                    empresa=normalize_company_field(parceiro.empresa),
                    tipo=parceiro.tipo,
                    telefone=parceiro.telefone,
                    email=parceiro.email,
                    comissao=parceiro.comissao,
                    created_at=parceiro.created_at,
                    updated_at=parceiro.updated_at,
                    negocios=[
                        NegocioResponse(
                            id=str(n.id),
                            empresa_terceira=n.empresa_terceira,
                            tipo=n.tipo,
                            qtd_licencas=n.qtd_licencas,
                            valor_negociacao=n.valor_negociacao,
                            tempo_contrato=n.tempo_contrato,
                            data_inicio=n.data_inicio,
                            data_pagamento=n.data_pagamento,
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
            raise HTTPException(status_code=404, detail="Parceiro not found")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            nome=parceiro.nome,
            empresa=normalize_company_field(parceiro.empresa),
            tipo=parceiro.tipo,
            telefone=parceiro.telefone,
            email=parceiro.email,
            comissao=parceiro.comissao,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    empresa_terceira=n.empresa_terceira,
                    tipo=n.tipo,
                    qtd_licencas=n.qtd_licencas,
                    valor_negociacao=n.valor_negociacao,
                    tempo_contrato=n.tempo_contrato,
                    data_inicio=n.data_inicio,
                    data_pagamento=n.data_pagamento,
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
        if "empresa" in parceiro_update.model_dump(exclude_unset=True):
            company_value = parceiro_update.empresa
            if company_value and isinstance(company_value, str):
                from app.repositories.team_repository import TeamRepository
                company_ref = await TeamRepository.resolve_company_reference(company_value, validate_status=True)
                if not company_ref:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Company '{company_value}' not found, is not linked, or is not active"
                    )
        
        parceiro = await ParceiroRepository.update(parceiro_id, parceiro_update)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro not found")
        
        # Get negocios for this parceiro
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return ParceiroWithNegociosResponse(
            id=str(parceiro.id),
            nome=parceiro.nome,
            empresa=normalize_company_field(parceiro.empresa),
            tipo=parceiro.tipo,
            telefone=parceiro.telefone,
            email=parceiro.email,
            comissao=parceiro.comissao,
            created_at=parceiro.created_at,
            updated_at=parceiro.updated_at,
            negocios=[
                NegocioResponse(
                    id=str(n.id),
                    empresa_terceira=n.empresa_terceira,
                    tipo=n.tipo,
                    qtd_licencas=n.qtd_licencas,
                    valor_negociacao=n.valor_negociacao,
                    tempo_contrato=n.tempo_contrato,
                    data_inicio=n.data_inicio,
                    data_pagamento=n.data_pagamento,
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
            raise HTTPException(status_code=404, detail="Parceiro not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting parceiro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEGOCIO ====================

@router.post("/parceiro/{parceiro_id}/negocio", response_model=NegocioResponse, status_code=201)
async def create_negocio(parceiro_id: str, negocio: NegocioCreate):
    """Creates a new Negocio for a Parceiro."""
    try:
        # Verify parceiro exists
        parceiro = await ParceiroRepository.get_by_id(parceiro_id)
        if not parceiro:
            raise HTTPException(status_code=404, detail="Parceiro not found")
        
        negocio_created = await NegocioRepository.create(negocio, parceiro_id)
        
        return NegocioResponse(
            id=str(negocio_created.id),
            empresa_terceira=negocio_created.empresa_terceira,
            tipo=negocio_created.tipo,
            qtd_licencas=negocio_created.qtd_licencas,
            valor_negociacao=negocio_created.valor_negociacao,
            tempo_contrato=negocio_created.tempo_contrato,
            data_inicio=negocio_created.data_inicio,
            data_pagamento=negocio_created.data_pagamento,
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
            raise HTTPException(status_code=404, detail="Parceiro not found")
        
        negocios = await NegocioRepository.list_by_parceiro(parceiro_id)
        
        return [
            NegocioResponse(
                id=str(n.id),
                empresa_terceira=n.empresa_terceira,
                tipo=n.tipo,
                qtd_licencas=n.qtd_licencas,
                valor_negociacao=n.valor_negociacao,
                tempo_contrato=n.tempo_contrato,
                data_inicio=n.data_inicio,
                data_pagamento=n.data_pagamento,
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
            empresa_terceira=negocio.empresa_terceira,
            tipo=negocio.tipo,
            qtd_licencas=negocio.qtd_licencas,
            valor_negociacao=negocio.valor_negociacao,
            tempo_contrato=negocio.tempo_contrato,
            data_inicio=negocio.data_inicio,
            data_pagamento=negocio.data_pagamento,
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
            empresa_terceira=negocio.empresa_terceira,
            tipo=negocio.tipo,
            qtd_licencas=negocio.qtd_licencas,
            valor_negociacao=negocio.valor_negociacao,
            tempo_contrato=negocio.tempo_contrato,
            data_inicio=negocio.data_inicio,
            data_pagamento=negocio.data_pagamento,
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

