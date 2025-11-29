"""Company history model for tracking changes."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.customer import PyObjectId


class CompanyHistoryChange(BaseModel):
    """Schema for a single field change."""
    old: Optional[Any] = Field(None, description="Old value")
    new: Optional[Any] = Field(None, description="New value")


class CompanyHistory(BaseModel):
    """Schema for company change history."""
    id: PyObjectId = Field(default_factory=lambda: PyObjectId(), alias="_id")
    company_id: PyObjectId = Field(..., description="ID of the company")
    action: str = Field(..., description="Action performed (created, updated, deleted)")
    changes: Optional[Dict[str, CompanyHistoryChange]] = Field(None, description="Dictionary of field changes")
    user: Optional[str] = Field(None, description="User who made the change")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the change occurred")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class CompanyHistoryCreate(BaseModel):
    """Schema for creating a company history entry."""
    company_id: str
    action: str
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    user: Optional[str] = None


class CompanyHistoryResponse(BaseModel):
    """Company history response schema."""
    id: str
    company_id: str
    action: str
    changes: Optional[Dict[str, Dict[str, Any]]] = None
    user: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


