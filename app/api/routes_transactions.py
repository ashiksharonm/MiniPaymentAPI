"""
Transaction API routes.

Handles HTTP endpoints for transaction management.
All business logic is delegated to the transaction service.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionStatusUpdate,
    TransactionListResponse,
)
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    get_transactions_by_user,
    update_transaction_status,
    TransactionNotFoundError,
    InvalidCurrencyError,
    FXConversionError,
    InvalidStatusTransitionError,
)
from app.services.user_service import UserNotFoundError

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
    description=(
        "Create a new transaction with automatic FX conversion. "
        "Providing an idempotency_key ensures the same transaction won't be created twice."
    )
)
def create_new_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    """
    Create a new transaction with FX conversion.
    
    - **user_id**: UUID of the user creating the transaction
    - **amount**: Amount to transfer (positive number)
    - **source_currency**: Source currency code (USD, EUR, INR, GBP)
    - **target_currency**: Target currency code (USD, EUR, INR, GBP)
    - **idempotency_key**: Optional key to prevent duplicate transactions
    
    The FX conversion is applied at creation time using static rates.
    If an idempotency_key is provided and a transaction with that key exists,
    the existing transaction is returned instead of creating a new one.
    """
    try:
        transaction = create_transaction(db, transaction_data)
        return TransactionResponse.model_validate(transaction)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (InvalidCurrencyError, FXConversionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Retrieve a transaction by its unique identifier."
)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    """
    Get a transaction by its UUID.
    
    - **transaction_id**: The unique identifier of the transaction
    
    Returns 404 if the transaction is not found.
    """
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found"
        )
    return TransactionResponse.model_validate(transaction)


@router.patch(
    "/{transaction_id}/status",
    response_model=TransactionResponse,
    summary="Update transaction status",
    description=(
        "Update the status of a transaction. "
        "Valid transitions: PENDING → COMPLETED, PENDING → FAILED"
    )
)
def update_status(
    transaction_id: str,
    status_update: TransactionStatusUpdate,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    """
    Update the status of a transaction.
    
    - **transaction_id**: The unique identifier of the transaction
    - **status**: New status (COMPLETED or FAILED)
    
    Only PENDING transactions can have their status updated.
    COMPLETED and FAILED are terminal states.
    """
    try:
        transaction = update_transaction_status(db, transaction_id, status_update.status)
        return TransactionResponse.model_validate(transaction)
    except TransactionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# User transactions endpoint (nested under users for REST convention)
user_transactions_router = APIRouter(tags=["Transactions"])


@user_transactions_router.get(
    "/users/{user_id}/transactions",
    response_model=TransactionListResponse,
    summary="List user transactions",
    description="Get all transactions for a specific user with pagination."
)
def list_user_transactions(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db)
) -> TransactionListResponse:
    """
    List all transactions for a user.
    
    - **user_id**: UUID of the user
    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum number of results (default: 100, max: 1000)
    
    Returns transactions in descending order by creation date.
    """
    try:
        transactions, total = get_transactions_by_user(db, user_id, skip, limit)
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in transactions],
            total=total
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
