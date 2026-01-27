"""
Pydantic schemas for Transaction API validation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.fx_rates import SUPPORTED_CURRENCIES


class TransactionStatus(str, Enum):
    """Transaction status values."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    
    user_id: str = Field(
        ..., 
        description="UUID of the user creating the transaction",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    amount: Decimal = Field(
        ..., 
        gt=0,
        description="Amount to transfer (must be positive)",
        examples=["100.00"]
    )
    
    source_currency: str = Field(
        ..., 
        min_length=3, 
        max_length=3,
        description="Source currency code (ISO 4217)",
        examples=["USD"]
    )
    
    target_currency: str = Field(
        ..., 
        min_length=3, 
        max_length=3,
        description="Target currency code (ISO 4217)",
        examples=["INR"]
    )
    
    idempotency_key: Optional[str] = Field(
        None,
        max_length=64,
        description="Optional key to prevent duplicate transactions",
        examples=["txn-12345-abc"]
    )
    
    @field_validator("source_currency", "target_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate and uppercase currency codes."""
        v_upper = v.upper()
        if v_upper not in SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Currency '{v}' not supported. "
                f"Supported currencies: {', '.join(sorted(SUPPORTED_CURRENCIES))}"
            )
        return v_upper
    
    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 4 decimal places."""
        # Quantize to 4 decimal places
        return v.quantize(Decimal("0.0001"))


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    
    id: str = Field(..., description="Unique transaction identifier (UUID)")
    user_id: str = Field(..., description="User who created the transaction")
    idempotency_key: Optional[str] = Field(None, description="Client-provided idempotency key")
    amount: Decimal = Field(..., description="Original amount in source currency")
    source_currency: str = Field(..., description="Source currency code")
    target_currency: str = Field(..., description="Target currency code")
    fx_rate: Decimal = Field(..., description="Exchange rate applied")
    converted_amount: Decimal = Field(..., description="Amount after conversion")
    status: TransactionStatus = Field(..., description="Current transaction status")
    created_at: datetime = Field(..., description="Timestamp when transaction was created")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "idempotency_key": "txn-12345-abc",
                "amount": "100.00",
                "source_currency": "USD",
                "target_currency": "INR",
                "fx_rate": "83.00",
                "converted_amount": "8300.00",
                "status": "PENDING",
                "created_at": "2024-01-27T10:35:00Z"
            }
        }
    }


class TransactionStatusUpdate(BaseModel):
    """Schema for updating transaction status."""
    
    status: TransactionStatus = Field(
        ...,
        description="New transaction status"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "COMPLETED"
            }
        }
    }


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    
    transactions: list[TransactionResponse]
    total: int = Field(..., description="Total number of transactions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "transactions": [],
                "total": 0
            }
        }
    }
