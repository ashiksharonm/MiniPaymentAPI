"""
Transaction SQLAlchemy model.

Represents a payment transaction with FX conversion.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionStatus(str, Enum):
    """
    Transaction status enum.
    
    - PENDING: Transaction created but not yet processed
    - COMPLETED: Transaction successfully processed
    - FAILED: Transaction failed during processing
    """
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transaction(Base):
    """
    Transaction model representing a payment with currency conversion.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: Reference to the user who created the transaction
        idempotency_key: Client-provided key to prevent duplicate transactions
        amount: Original amount in source currency
        source_currency: Currency of the original amount (e.g., 'USD')
        target_currency: Currency to convert to (e.g., 'INR')
        fx_rate: Exchange rate applied at transaction creation
        converted_amount: Amount after FX conversion
        status: Current transaction status (PENDING/COMPLETED/FAILED)
        created_at: Timestamp when the transaction was created
    """
    __tablename__ = "transactions"
    
    # Primary key as UUID
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Idempotency key for preventing duplicate transactions
    # Client should provide this, it's optional but recommended
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True
    )
    
    # Amount fields using Decimal for precision
    # Numeric(18, 4) allows for large amounts with 4 decimal places
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )
    
    source_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )
    
    target_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )
    
    fx_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),  # High precision for FX rates
        nullable=False
    )
    
    converted_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )
    
    # Status with default PENDING
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TransactionStatus.PENDING.value,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    
    # Composite index for efficient user+status queries
    __table_args__ = (
        Index("ix_transactions_user_status", "user_id", "status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount} {self.source_currency}, status={self.status})>"
        )


# Import User to resolve forward reference
from app.models.user import User  # noqa: E402, F401
