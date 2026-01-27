"""
User SQLAlchemy model.

Represents a user who can create and manage transactions.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """
    User model representing a customer in the payments system.
    
    Attributes:
        id: Unique identifier (UUID)
        name: User's full name
        email: User's email (unique, used for identification)
        country: User's country code (e.g., 'US', 'IN', 'GB')
        created_at: Timestamp when the user was created
    """
    __tablename__ = "users"
    
    # Primary key as UUID stored as string for SQLite compatibility
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationship to transactions (one-to-many)
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


# Import Transaction here to resolve forward reference
from app.models.transaction import Transaction  # noqa: E402, F401
