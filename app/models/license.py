"""License model."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.customer import PyObjectId


class LicenseBase(BaseModel):
    """Base License schema."""
    customer_id: PyObjectId = Field(..., description="Associated customer ID")
    license_type: str = Field(..., pattern="^(Start|Hub)$", description="License type: Start or Hub")
    status: str = Field(default="active", pattern="^(active|inactive|cancelled)$", description="License status")
    portal_id: Optional[str] = Field(None, description="License ID in the License Portal (CCD)")


class LicenseCreate(LicenseBase):
    """Schema for creating a License."""
    pass


class LicenseUpdate(BaseModel):
    """Schema for updating a License."""
    license_type: Optional[str] = Field(None, pattern="^(Start|Hub)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|cancelled)$")
    portal_id: Optional[str] = None


class License(LicenseBase):
    """Complete License schema."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "customer_id": "507f1f77bcf86cd799439011",
                "license_type": "Hub",
                "status": "active",
                "portal_id": "LIC-12345"
            }
        }
    }


class LicenseResponse(BaseModel):
    """License response schema."""
    id: str
    customer_id: str
    license_type: str
    status: str
    portal_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookLicenseCreated(BaseModel):
    """Webhook schema for license created event."""
    event: str = Field(default="license-created", description="Event type")
    portal_id: str = Field(..., description="License ID in the Portal")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    license_type: str = Field(..., pattern="^(Start|Hub)$", description="License type")
    extra_data: Optional[dict] = Field(default_factory=dict, description="Additional webhook data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "event": "license-created",
                "portal_id": "LIC-12345",
                "customer_email": "john.doe@example.com",
                "customer_phone": "5511999999999",
                "license_type": "Hub",
                "extra_data": {}
            }
        }
    }

