"""
Pydantic schemas for User API validation.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="User's full name",
        examples=["John Doe"]
    )
    
    email: EmailStr = Field(
        ..., 
        description="User's email address (must be unique)",
        examples=["john.doe@example.com"]
    )
    
    country: str = Field(
        ..., 
        min_length=2, 
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
        examples=["US", "IN", "GB"]
    )
    
    @field_validator("country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        """Ensure country code is uppercase."""
        return v.upper()


class UserResponse(BaseModel):
    """Schema for user response."""
    
    id: str = Field(..., description="Unique user identifier (UUID)")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    country: str = Field(..., description="User's country code")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john.doe@example.com", 
                "country": "US",
                "created_at": "2024-01-27T10:30:00Z"
            }
        }
    }
