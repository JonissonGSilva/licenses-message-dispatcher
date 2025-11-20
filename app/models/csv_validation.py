"""Models for CSV validation results."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class InvalidRowDetail(BaseModel):
    """Details of an invalid CSV row."""
    row_number: int = Field(..., description="Row number in the CSV (1-indexed, including header)")
    raw_data: Dict[str, Any] = Field(..., description="Raw data from the CSV row")
    errors: list[str] = Field(..., description="List of validation errors for this row")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "row_number": 3,
                "raw_data": {
                    "name": "",
                    "email": "test@example.com",
                    "phone": "123",
                    "license_type": "Invalid",
                    "company": "Test Company"
                },
                "errors": [
                    "Name cannot be empty",
                    "Invalid or missing phone (value: '123')",
                    "Invalid license type (value: 'Invalid', must be 'Start' or 'Hub')"
                ]
            }
        }
    }


class CSVValidationResult(BaseModel):
    """Result of CSV validation."""
    total_rows: int = Field(..., description="Total number of rows in CSV (excluding header)")
    valid_rows: int = Field(..., description="Number of valid rows")
    invalid_rows: int = Field(..., description="Number of invalid rows")
    invalid_rows_details: list[InvalidRowDetail] = Field(default_factory=list, description="Detailed information about invalid rows")
    has_errors: bool = Field(..., description="Whether there are any validation errors")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_rows": 10,
                "valid_rows": 7,
                "invalid_rows": 3,
                "has_errors": True,
                "invalid_rows_details": [
                    {
                        "row_number": 3,
                        "raw_data": {"name": "", "phone": "123"},
                        "errors": ["Name cannot be empty", "Invalid phone"]
                    }
                ]
            }
        }
    }

