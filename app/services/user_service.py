"""
User service layer.

Contains all business logic for user operations.
No database operations should happen in the API routes - only here.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate


class UserServiceError(Exception):
    """Base exception for user service errors."""
    pass


class DuplicateEmailError(UserServiceError):
    """Raised when attempting to create a user with an existing email."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when a user is not found."""
    pass


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_data: Validated user creation data
        
    Returns:
        The created User model instance
        
    Raises:
        DuplicateEmailError: If a user with the same email already exists
    """
    # Check for existing email first (for better error message)
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise DuplicateEmailError(f"User with email '{user_data.email}' already exists")
    
    # Create user model from schema
    user = User(
        name=user_data.name,
        email=user_data.email,
        country=user_data.country
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        # Handle race condition where email was created between check and insert
        db.rollback()
        raise DuplicateEmailError(f"User with email '{user_data.email}' already exists")


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Get a user by their ID.
    
    Args:
        db: Database session
        user_id: UUID of the user
        
    Returns:
        The User model instance, or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by their email.
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        The User model instance, or None if not found
    """
    return db.query(User).filter(User.email == email).first()


def get_user_or_raise(db: Session, user_id: str) -> User:
    """
    Get a user by ID, raising an exception if not found.
    
    Args:
        db: Database session
        user_id: UUID of the user
        
    Returns:
        The User model instance
        
    Raises:
        UserNotFoundError: If the user is not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundError(f"User with ID '{user_id}' not found")
    return user
