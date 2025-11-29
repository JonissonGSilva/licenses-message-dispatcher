"""Team models for Direta, Indicador, Parceiro and Negocio."""
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator
from bson import ObjectId
from app.models.customer import PyObjectId, CompanyReference
import re


class NegocioBase(BaseModel):
    """Base Negocio schema."""
    empresa_terceira: str = Field(..., min_length=1, max_length=200, description="Third-party company name")
    tipo: str = Field(..., pattern="^(Pré-Pago|Pós-Pago)$", description="Type: Pré-Pago or Pós-Pago")
    qtd_licencas: int = Field(..., ge=1, description="Number of licenses")
    valor_negociacao: str = Field(..., min_length=1, max_length=50, description="Negotiation value")
    tempo_contrato: str = Field(..., min_length=1, max_length=50, description="Contract duration")
    data_inicio: datetime = Field(..., description="Start date")
    data_pagamento: datetime = Field(..., description="Payment date")


class NegocioCreate(NegocioBase):
    """Schema for creating a Negocio."""
    pass


class NegocioUpdate(BaseModel):
    """Schema for updating a Negocio."""
    empresa_terceira: Optional[str] = Field(None, min_length=1, max_length=200)
    tipo: Optional[str] = Field(None, pattern="^(Pré-Pago|Pós-Pago)$")
    qtd_licencas: Optional[int] = Field(None, ge=1)
    valor_negociacao: Optional[str] = Field(None, min_length=1, max_length=50)
    tempo_contrato: Optional[str] = Field(None, min_length=1, max_length=50)
    data_inicio: Optional[datetime] = None
    data_pagamento: Optional[datetime] = None


class Negocio(NegocioBase):
    """Complete Negocio schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class NegocioResponse(BaseModel):
    """Negocio response schema."""
    id: str
    empresa_terceira: str
    tipo: str
    qtd_licencas: int
    valor_negociacao: str
    tempo_contrato: str
    data_inicio: datetime
    data_pagamento: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class DiretaBase(BaseModel):
    """Base Direta schema."""
    nome: str = Field(..., min_length=1, max_length=200, description="Full name")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF (Brazilian ID) - 11 digits")
    telefone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address")
    tipo: str = Field(..., pattern="^(sócio|colaborador)$", description="Type: sócio or colaborador")
    funcao: str = Field(..., min_length=1, max_length=100, description="Job function")
    remuneracao: str = Field(..., min_length=1, max_length=50, description="Remuneration")
    comissao: str = Field(..., min_length=1, max_length=200, description="Commission policy")
    
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
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    tipo: Optional[str] = Field(None, pattern="^(sócio|colaborador)$")
    funcao: Optional[str] = Field(None, min_length=1, max_length=100)
    remuneracao: Optional[str] = Field(None, min_length=1, max_length=50)
    comissao: Optional[str] = Field(None, min_length=1, max_length=200)
    
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class DiretaResponse(BaseModel):
    """Direta response schema."""
    id: str
    nome: str
    cpf: str
    telefone: str
    email: str
    tipo: str
    funcao: str
    remuneracao: str
    comissao: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class IndicadorBase(BaseModel):
    """Base Indicador schema."""
    nome: str = Field(..., min_length=1, max_length=200, description="Full name")
    empresa: Optional[Union[str, CompanyReference, dict]] = Field(None, description="Company name (string) or Company reference")
    telefone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address")
    comissao: str = Field(..., min_length=1, max_length=200, description="Commission policy")


class IndicadorCreate(IndicadorBase):
    """Schema for creating an Indicador."""
    pass


class IndicadorUpdate(BaseModel):
    """Schema for updating an Indicador."""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    empresa: Optional[Union[str, CompanyReference, dict]] = None
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    comissao: Optional[str] = Field(None, min_length=1, max_length=200)


class Indicador(IndicadorBase):
    """Complete Indicador schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class IndicadorResponse(BaseModel):
    """Indicador response schema."""
    id: str
    nome: str
    empresa: Optional[Union[str, dict]]
    telefone: str
    email: str
    comissao: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }


class ParceiroBase(BaseModel):
    """Base Parceiro schema."""
    nome: str = Field(..., min_length=1, max_length=200, description="Full name")
    empresa: Optional[Union[str, CompanyReference, dict]] = Field(None, description="Company name (string) or Company reference")
    tipo: str = Field(..., pattern="^(Agente autorizado|Sindicato|Prefeitura)$", description="Type: Agente autorizado, Sindicato or Prefeitura")
    telefone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address")
    comissao: str = Field(..., pattern="^(Ouro|Prata|Bronze)$", description="Commission: Ouro, Prata or Bronze")


class ParceiroCreate(ParceiroBase):
    """Schema for creating a Parceiro."""
    pass


class ParceiroUpdate(BaseModel):
    """Schema for updating a Parceiro."""
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    empresa: Optional[Union[str, CompanyReference, dict]] = None
    tipo: Optional[str] = Field(None, pattern="^(Agente autorizado|Sindicato|Prefeitura)$")
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    comissao: Optional[str] = Field(None, pattern="^(Ouro|Prata|Bronze)$")


class Parceiro(ParceiroBase):
    """Complete Parceiro schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class ParceiroResponse(BaseModel):
    """Parceiro response schema."""
    id: str
    nome: str
    empresa: Optional[Union[str, dict]]
    tipo: str
    telefone: str
    email: str
    comissao: str
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

