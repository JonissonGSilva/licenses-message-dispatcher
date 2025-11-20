"""Customer model."""
from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId


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


class CustomerBase(BaseModel):
    """Base Customer schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Customer full name")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone with area code and country code")
    license_type: str = Field(..., pattern="^(Start|Hub)$", description="License type: Start or Hub")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    active: bool = Field(default=True, description="Indicates if the customer is active")


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


class CustomerResponse(BaseModel):
    """Customer response schema."""
    id: str
    name: str
    email: Optional[str]
    phone: str
    license_type: str
    company: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

