"""Company model."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.customer import PyObjectId


class CompanyBase(BaseModel):
    """Base Company schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    cnpj: Optional[str] = Field(None, max_length=18, description="CNPJ (Brazilian company ID)")
    email: Optional[str] = Field(None, max_length=200, description="Company email")
    phone: Optional[str] = Field(None, max_length=20, description="Company phone")
    address: Optional[str] = Field(None, max_length=500, description="Company address")
    city: Optional[str] = Field(None, max_length=100, description="Company city")
    state: Optional[str] = Field(None, max_length=2, description="Company state (2 letters)")
    zip_code: Optional[str] = Field(None, max_length=10, description="ZIP code")
    linked: bool = Field(default=False, description="Indicates if the company is linked/associated")
    active: bool = Field(default=True, description="Indicates if the company is active")
    license_timeout: Optional[int] = Field(None, ge=0, description="License timeout in seconds")
    contract_expiration: Optional[datetime] = Field(None, description="Contract expiration date")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$", description="License type: Start or Hub")
    portal_id: Optional[str] = Field(None, description="Company ID in the License Portal")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about the company")


class CompanyCreate(CompanyBase):
    """Schema for creating a Company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a Company."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cnpj: Optional[str] = Field(None, max_length=18)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    linked: Optional[bool] = None
    active: Optional[bool] = None
    license_timeout: Optional[int] = Field(None, ge=0)
    contract_expiration: Optional[datetime] = None
    employee_count: Optional[int] = Field(None, ge=0)
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$")
    portal_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)


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
                "cnpj": "12.345.678/0001-90",
                "email": "contato@empresaxyz.com.br",
                "phone": "5511999999999",
                "address": "Rua Exemplo, 123",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01234-567",
                "linked": True,
                "active": True,
                "license_timeout": 3600,
                "contract_expiration": "2024-12-31T23:59:59",
                "employee_count": 150,
                "license_type": "Hub",
                "portal_id": "COMP-12345",
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
    license_timeout: Optional[int]
    contract_expiration: Optional[datetime]
    employee_count: Optional[int]
    license_type: Optional[str]
    portal_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

