"""Company model."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.customer import PyObjectId


class ContractRenovated(BaseModel):
    """Schema for contract renovation record."""
    age_contract: int = Field(..., description="Age of the contract in months or days")
    type_contract: int = Field(..., description="Type of contract (1, 2, 3, etc.)")
    isExpirated: bool = Field(default=False, description="Indicates if the contract is expired")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyBase(BaseModel):
    """Base Company schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    cnpj: str = Field(..., min_length=14, max_length=14, description="CNPJ (Brazilian company ID) - 14 digits")
    email: Optional[str] = Field(None, max_length=200, description="Company email")
    phone: Optional[str] = Field(None, max_length=20, description="Company phone")
    address: Optional[str] = Field(None, max_length=500, description="Company address")
    city: Optional[str] = Field(None, max_length=100, description="Company city")
    state: Optional[str] = Field(None, max_length=2, description="Company state (2 letters)")
    zip_code: Optional[str] = Field(None, max_length=10, description="ZIP code")
    linked: bool = Field(default=False, description="Indicates if the company is linked/associated")
    active: bool = Field(default=True, description="Indicates if the company is active (legacy field)")
    status: Optional[str] = Field(default="ativo", pattern="^(ativo|suspenso|em_negociacao)$", description="Company status: ativo, suspenso, em_negociacao")
    contract_expiration: Optional[datetime] = Field(None, description="Contract expiration date")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$", description="License type: Start or Hub")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the company")
    contract_renovated: Optional[List[ContractRenovated]] = Field(default_factory=list, description="Array of contract renovation records")
    isActive: Optional[bool] = Field(None, description="Indicates if the company is currently active (legacy field, use 'active' instead)")


class CompanyCreate(CompanyBase):
    """Schema for creating a Company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a Company."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cnpj: Optional[str] = Field(None, min_length=14, max_length=14)
    status: Optional[str] = Field(None, pattern="^(ativo|suspenso|em_negociacao)$")
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    linked: Optional[bool] = None
    active: Optional[bool] = None
    contract_expiration: Optional[datetime] = None
    employee_count: Optional[int] = Field(None, ge=0)
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$")
    notes: Optional[str] = Field(None, max_length=1000)
    contract_renovated: Optional[List[ContractRenovated]] = None
    isActive: Optional[bool] = None


class Company(CompanyBase):
    """Complete Company schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Empresa XYZ Ltda",
                "cnpj": "12345678000190",
                "email": "contato@empresaxyz.com.br",
                "phone": "5511999999999",
                "address": "Rua Exemplo, 123",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01234-567",
                "linked": True,
                "active": True,
                "contract_expiration": "2024-12-31T23:59:59",
                "employee_count": 150,
                "license_type": "Hub",
                "notes": "Cliente premium"
            }
        }
    }


class CompanyResponse(BaseModel):
    """Company response schema."""
    id: str
    name: str
    cnpj: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    linked: bool
    active: bool
    status: Optional[str]
    contract_expiration: Optional[datetime]
    employee_count: Optional[int]
    license_type: Optional[str]
    notes: Optional[str]
    contract_renovated: Optional[List[ContractRenovated]]
    isActive: Optional[bool]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanyPaginatedResponse(BaseModel):
    """Paginated company response schema."""
    data: List[CompanyResponse]
    total: int
    page: int
    limit: int



