"""Team models for Direta, Indicador, Parceiro and Negocio."""
from typing import Optional, List, Union, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, field_validator
from bson import ObjectId
from app.models.customer import PyObjectId, CompanyReference
import re


class NegocioBase(BaseModel):
    """Base Negocio schema."""
    third_party_company: str = Field(..., min_length=1, max_length=200, description="Third-party company name", alias="empresa_terceira")
    type: str = Field(..., pattern="^(Pré-Pago|Pós-Pago)$", description="Type: Pré-Pago or Pós-Pago", alias="tipo")
    license_count: int = Field(..., ge=1, description="Number of licenses", alias="qtd_licencas")
    negotiation_value: str = Field(..., min_length=1, max_length=50, description="Negotiation value", alias="valor_negociacao")
    contract_duration: str = Field(..., min_length=1, max_length=50, description="Contract duration", alias="tempo_contrato")
    start_date: datetime = Field(..., description="Start date", alias="data_inicio")
    payment_date: datetime = Field(..., description="Payment date", alias="data_pagamento")
    
    model_config = {
        "populate_by_name": True,
    }


class NegocioCreate(NegocioBase):
    """Schema for creating a Negocio."""
    pass


class NegocioUpdate(BaseModel):
    """Schema for updating a Negocio."""
    third_party_company: Optional[str] = Field(None, min_length=1, max_length=200, alias="empresa_terceira")
    type: Optional[str] = Field(None, pattern="^(Pré-Pago|Pós-Pago)$", alias="tipo")
    license_count: Optional[int] = Field(None, ge=1, alias="qtd_licencas")
    negotiation_value: Optional[str] = Field(None, min_length=1, max_length=50, alias="valor_negociacao")
    contract_duration: Optional[str] = Field(None, min_length=1, max_length=50, alias="tempo_contrato")
    start_date: Optional[datetime] = Field(None, alias="data_inicio")
    payment_date: Optional[datetime] = Field(None, alias="data_pagamento")
    
    model_config = {
        "populate_by_name": True,
    }


class Negocio(NegocioBase):
    """Complete Negocio schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class NegocioResponse(BaseModel):
    """Negocio response schema."""
    id: str
    third_party_company: str
    type: str
    license_count: int
    negotiation_value: str
    contract_duration: str
    start_date: datetime
    payment_date: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class DiretaBase(BaseModel):
    """Base Direta schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Full name", alias="nome")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF (Brazilian ID) - 11 digits")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number", alias="telefone")
    email: EmailStr = Field(..., description="Email address")
    type: str = Field(..., pattern="^(sócio|colaborador)$", description="Type: sócio or colaborador", alias="tipo")
    function: str = Field(..., min_length=1, max_length=100, description="Job function", alias="funcao")
    remuneration: str = Field(..., min_length=1, max_length=50, description="Remuneration", alias="remuneracao")
    commission: str = Field(..., min_length=1, max_length=200, description="Commission policy", alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }
    
    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Validates CPF: must be 11 digits."""
        if not v or not v.strip():
            raise ValueError("CPF é obrigatório")
        # Remove non-numeric characters
        numbers = re.sub(r'\D', '', v)
        if len(numbers) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return numbers


class DiretaCreate(DiretaBase):
    """Schema for creating a Direta."""
    pass


class DiretaUpdate(BaseModel):
    """Schema for updating a Direta."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, alias="nome")
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    phone: Optional[str] = Field(None, min_length=10, max_length=20, alias="telefone")
    email: Optional[EmailStr] = None
    type: Optional[str] = Field(None, pattern="^(sócio|colaborador)$", alias="tipo")
    function: Optional[str] = Field(None, min_length=1, max_length=100, alias="funcao")
    remuneration: Optional[str] = Field(None, min_length=1, max_length=50, alias="remuneracao")
    commission: Optional[str] = Field(None, min_length=1, max_length=200, alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }
    
    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Validates CPF: must be 11 digits."""
        if v is None:
            return v
        if not v.strip():
            return None
        # Remove non-numeric characters
        numbers = re.sub(r'\D', '', v)
        if len(numbers) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return numbers


class Direta(DiretaBase):
    """Complete Direta schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class DiretaResponse(BaseModel):
    """Direta response schema."""
    id: str
    name: str
    cpf: str
    phone: str
    email: str
    type: str
    function: str
    remuneration: str
    commission: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class IndicadorBase(BaseModel):
    """Base Indicador schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Full name", alias="nome")
    company: Optional[List[Union[CompanyReference, dict]]] = Field(default_factory=list, description="List of company references", alias="empresa")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number", alias="telefone")
    email: EmailStr = Field(..., description="Email address")
    commission: str = Field(..., min_length=1, max_length=200, description="Commission policy", alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }


class IndicadorCreate(IndicadorBase):
    """Schema for creating an Indicador."""
    pass


class IndicadorUpdate(BaseModel):
    """Schema for updating an Indicador."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, alias="nome")
    company: Optional[List[Union[CompanyReference, dict]]] = Field(None, alias="empresa")
    phone: Optional[str] = Field(None, min_length=10, max_length=20, alias="telefone")
    email: Optional[EmailStr] = None
    commission: Optional[str] = Field(None, min_length=1, max_length=200, alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }


class Indicador(IndicadorBase):
    """Complete Indicador schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class IndicadorResponse(BaseModel):
    """Indicador response schema."""
    id: str
    name: str
    company: Optional[List[dict]] = Field(default_factory=list)
    phone: str
    email: str
    commission: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class ParceiroBase(BaseModel):
    """Base Parceiro schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Full name", alias="nome")
    company: Optional[List[Union[CompanyReference, dict]]] = Field(default_factory=list, description="List of company references", alias="empresa")
    type: str = Field(..., pattern="^(Agente autorizado|Sindicato|Prefeitura)$", description="Type: Agente autorizado, Sindicato or Prefeitura", alias="tipo")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number", alias="telefone")
    email: EmailStr = Field(..., description="Email address")
    commission: str = Field(..., pattern="^(Ouro|Prata|Bronze)$", description="Commission: Ouro, Prata or Bronze", alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }


class ParceiroCreate(ParceiroBase):
    """Schema for creating a Parceiro."""
    pass


class ParceiroUpdate(BaseModel):
    """Schema for updating a Parceiro."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, alias="nome")
    company: Optional[List[Union[CompanyReference, dict]]] = Field(None, alias="empresa")
    type: Optional[str] = Field(None, pattern="^(Agente autorizado|Sindicato|Prefeitura)$", alias="tipo")
    phone: Optional[str] = Field(None, min_length=10, max_length=20, alias="telefone")
    email: Optional[EmailStr] = None
    commission: Optional[str] = Field(None, pattern="^(Ouro|Prata|Bronze)$", alias="comissao")
    
    model_config = {
        "populate_by_name": True,
    }


class Parceiro(ParceiroBase):
    """Complete Parceiro schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class ParceiroResponse(BaseModel):
    """Parceiro response schema."""
    id: str
    name: str
    company: Optional[List[dict]] = Field(default_factory=list)
    type: str
    phone: str
    email: str
    commission: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class ParceiroWithNegociosResponse(ParceiroResponse):
    """Parceiro response with negocios."""
    negocios: List[NegocioResponse] = Field(default_factory=list)


# Paginated responses
class DiretaPaginatedResponse(BaseModel):
    """Paginated response for Direta."""
    data: List[DiretaResponse]
    total: int
    page: int
    limit: int


class IndicadorPaginatedResponse(BaseModel):
    """Paginated response for Indicador."""
    data: List[IndicadorResponse]
    total: int
    page: int
    limit: int


class ParceiroPaginatedResponse(BaseModel):
    """Paginated response for Parceiro."""
    data: List[ParceiroWithNegociosResponse]
    total: int
    page: int
    limit: int

