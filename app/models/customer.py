"""Customer model."""
from typing import Optional, Annotated, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, GetCoreSchemaHandler, field_validator
from pydantic_core import core_schema
from bson import ObjectId
import re


class PyObjectId(ObjectId):
    """Helper class for MongoDB ObjectId compatible with Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate_value(value):
            """Validates and converts value to PyObjectId."""
            if isinstance(value, ObjectId):
                return cls(value)
            if isinstance(value, str):
                if not ObjectId.is_valid(value):
                    raise ValueError("Invalid ObjectId")
                return cls(value)
            if isinstance(value, cls):
                return value
            raise ValueError(f"Invalid ObjectId: expected ObjectId or str, got {type(value)}")
        
        from_str_schema = core_schema.no_info_after_validator_function(
            validate_value,
            core_schema.str_schema()
        )
        
        from_objectid_schema = core_schema.no_info_after_validator_function(
            validate_value,
            core_schema.is_instance_schema(ObjectId)
        )
        
        return core_schema.union_schema([
            from_str_schema,
            from_objectid_schema
        ])


class CompanyReference(BaseModel):
    """Reference to a Company with ID and name."""
    id: PyObjectId = Field(..., description="Company ID (ObjectId)")
    name: str = Field(..., description="Company name")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "TechSolutions Ltda"
            }
        }
    }


class CustomerBase(BaseModel):
    """Base Customer schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Customer full name")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone with area code and country code")
    license_type: str = Field(..., pattern="^(Start|Hub)$", description="License type: Start or Hub")
    company: Optional[Union[str, CompanyReference, dict]] = Field(None, description="Company name (string) or Company reference (object with id and name)")
    active: bool = Field(default=True, description="Indicates if the customer is active")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validates customer name: minimum 2 words, each word with minimum 2 characters, no numbers."""
        if not v or not v.strip():
            raise ValueError("Nome é obrigatório")
        
        # Verificar se contém números
        if re.search(r'\d', v):
            raise ValueError("O nome não pode conter números")
        
        # Dividir em palavras (removendo espaços extras)
        words = [word for word in v.strip().split() if word]
        
        # Verificar se tem pelo menos 2 palavras
        if len(words) < 2:
            raise ValueError("O nome deve conter pelo menos 2 palavras")
        
        # Verificar se cada palavra tem pelo menos 2 caracteres
        invalid_words = [word for word in words if len(word) < 2]
        if invalid_words:
            raise ValueError("Cada palavra do nome deve ter pelo menos 2 caracteres")
        
        return v


class CustomerCreate(CustomerBase):
    """Schema for creating a Customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a Customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$")
    company: Optional[str] = Field(None, max_length=200)
    active: Optional[bool] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validates customer name: minimum 2 words, each word with minimum 2 characters, no numbers."""
        if v is None:
            return v
        
        if not v.strip():
            raise ValueError("Nome não pode ser vazio")
        
        # Verificar se contém números
        if re.search(r'\d', v):
            raise ValueError("O nome não pode conter números")
        
        # Dividir em palavras (removendo espaços extras)
        words = [word for word in v.strip().split() if word]
        
        # Verificar se tem pelo menos 2 palavras
        if len(words) < 2:
            raise ValueError("O nome deve conter pelo menos 2 palavras")
        
        # Verificar se cada palavra tem pelo menos 2 caracteres
        invalid_words = [word for word in words if len(word) < 2]
        if invalid_words:
            raise ValueError("Cada palavra do nome deve ter pelo menos 2 caracteres")
        
        return v


class AssociateCompanyRequest(BaseModel):
    """Schema for associating a company to a customer."""
    company_id: Optional[str] = Field(None, description="Company ID (ObjectId as string)")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "company_id": "6920a1c5cd2bf3399bbd3836"
            }
        }
    }


class Customer(CustomerBase):
    """Complete Customer schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "5511999999999",
                "license_type": "Hub",
                "company": "Company XYZ",
                "active": True
            }
        }
    }


def normalize_company_field(company_value: Any) -> Optional[Union[str, dict]]:
    """
    Normalizes company field to be either string or dict with string id.
    
    Args:
        company_value: Company value (can be str, dict, CompanyReference, or None)
        
    Returns:
        Normalized company value (str or dict with string id)
    """
    if company_value is None:
        return None
    
    if isinstance(company_value, str):
        return company_value
    
    if isinstance(company_value, dict):
        # Convert ObjectId to string if present
        result = company_value.copy()
        if "id" in result:
            result["id"] = str(result["id"])
        return result
    
    # If it's a CompanyReference or other Pydantic model, convert to dict
    if hasattr(company_value, "model_dump"):
        result = company_value.model_dump()
        if "id" in result:
            result["id"] = str(result["id"])
        return result
    
    # Fallback: convert to string
    return str(company_value)


class CustomerResponse(BaseModel):
    """Customer response schema."""
    id: str
    name: str
    email: Optional[str]
    phone: str
    license_type: str
    company: Optional[Union[str, dict]] = Field(None, description="Company name (string) or Company reference (object with id as string and name)")
    active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }
    
    @classmethod
    def from_customer(cls, customer: "Customer") -> "CustomerResponse":
        """Creates CustomerResponse from Customer, normalizing company field."""
        return cls(
            id=str(customer.id),
            name=customer.name,
            email=customer.email,
            phone=customer.phone,
            license_type=customer.license_type,
            company=normalize_company_field(customer.company),
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )

