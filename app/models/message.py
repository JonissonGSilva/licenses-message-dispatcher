"""Message model."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.customer import PyObjectId


class MessageBase(BaseModel):
    """Base Message schema."""
    customer_id: Optional[PyObjectId] = Field(None, description="Recipient customer ID")
    phone: str = Field(..., min_length=10, max_length=20, description="Recipient phone")
    license_type: str = Field(..., pattern="^(Start|Hub)$", description="License type for segmentation")
    content: str = Field(..., min_length=1, description="Message content")
    message_type: str = Field(default="hsm", pattern="^(hsm|text)$", description="Message type: HSM or text")
    status: str = Field(default="pending", pattern="^(pending|sent|failed)$", description="Send status")
    whatsapp_message_id: Optional[str] = Field(None, description="Message ID returned by WhatsApp API")
    error: Optional[str] = Field(None, description="Error message, if any")


class MessageCreate(MessageBase):
    """Schema for creating a Message."""
    pass


class MessageUpdate(BaseModel):
    """Schema for updating a Message."""
    status: Optional[str] = Field(None, pattern="^(pending|sent|failed)$")
    whatsapp_message_id: Optional[str] = None
    error: Optional[str] = None


class Message(MessageBase):
    """Complete Message schema."""
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
                "phone": "5511999999999",
                "license_type": "Hub",
                "content": "Welcome to Hub!",
                "message_type": "hsm",
                "status": "sent"
            }
        }
    }


class MessageResponse(BaseModel):
    """Message response schema."""
    id: str
    customer_id: Optional[str]
    phone: str
    license_type: str
    content: str
    message_type: str
    status: str
    whatsapp_message_id: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

