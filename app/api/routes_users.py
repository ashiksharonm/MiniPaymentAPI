"""
User API routes.

Handles HTTP endpoints for user management.
All business logic is delegated to the user service.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import (
    create_user,
    get_user_by_id,
    DuplicateEmailError,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided details. Email must be unique."
)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Create a new user.
    
    - **name**: User's full name (1-100 characters)
    - **email**: User's email address (must be unique)
    - **country**: ISO 3166-1 alpha-2 country code (e.g., US, IN, GB)
    
    Returns the created user with a generated UUID.
    """
    try:
        user = create_user(db, user_data)
        return UserResponse.model_validate(user)
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a user by their unique identifier."
)
def get_user(
    user_id: str,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get a user by their UUID.
    
    - **user_id**: The unique identifier of the user
    
    Returns 404 if the user is not found.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )
    return UserResponse.model_validate(user)
