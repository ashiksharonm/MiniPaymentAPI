"""
Transaction service layer.

Contains all business logic for transaction operations including FX conversion.
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import TransactionCreate, TransactionStatus as SchemaTransactionStatus
from app.services.user_service import get_user_or_raise, UserNotFoundError
from app.core.fx_rates import convert_currency, is_currency_supported
from app.core.redis_client import get_idempotent_transaction, set_idempotent_transaction


class TransactionServiceError(Exception):
    """Base exception for transaction service errors."""
    pass


class TransactionNotFoundError(TransactionServiceError):
    """Raised when a transaction is not found."""
    pass


class InvalidCurrencyError(TransactionServiceError):
    """Raised when an invalid currency is provided."""
    pass


class FXConversionError(TransactionServiceError):
    """Raised when FX conversion fails."""
    pass


class DuplicateIdempotencyKeyError(TransactionServiceError):
    """Raised when a duplicate idempotency key is detected."""
    pass


class InvalidStatusTransitionError(TransactionServiceError):
    """Raised when an invalid status transition is attempted."""
    pass


def create_transaction(db: Session, transaction_data: TransactionCreate) -> Transaction:
    """
    Create a new transaction with FX conversion.
    
    This operation is idempotent if an idempotency_key is provided.
    If a transaction with the same idempotency_key already exists, it is returned.
    
    Args:
        db: Database session
        transaction_data: Validated transaction creation data
        
    Returns:
        The created (or existing) Transaction model instance
        
    Raises:
        UserNotFoundError: If the user_id doesn't exist
        InvalidCurrencyError: If currencies are not supported
        FXConversionError: If FX conversion fails
    """
    # Validate user exists
    get_user_or_raise(db, transaction_data.user_id)
    
    # Check idempotency key in Redis first for O(1) high-speed validation
    if transaction_data.idempotency_key:
        cached_txn = get_idempotent_transaction(transaction_data.idempotency_key)
        if cached_txn:
            # Reconstruct dummy ORM object out of cached dict to satisfy router validation
            txn = Transaction(**cached_txn)
            return txn
            
        # Fallback to DB check (in case Redis crashed/evicted early)
        existing = get_transaction_by_idempotency_key(db, transaction_data.idempotency_key)
        if existing:
            return existing
    
    # Validate currencies
    if not is_currency_supported(transaction_data.source_currency):
        raise InvalidCurrencyError(f"Source currency '{transaction_data.source_currency}' not supported")
    if not is_currency_supported(transaction_data.target_currency):
        raise InvalidCurrencyError(f"Target currency '{transaction_data.target_currency}' not supported")
    
    # Perform FX conversion
    converted_amount, fx_rate = convert_currency(
        transaction_data.amount,
        transaction_data.source_currency,
        transaction_data.target_currency
    )
    
    if converted_amount is None or fx_rate is None:
        raise FXConversionError(
            f"Unable to convert {transaction_data.source_currency} to {transaction_data.target_currency}"
        )
    
    # Create transaction
    transaction = Transaction(
        user_id=transaction_data.user_id,
        idempotency_key=transaction_data.idempotency_key,
        amount=transaction_data.amount,
        source_currency=transaction_data.source_currency.upper(),
        target_currency=transaction_data.target_currency.upper(),
        fx_rate=fx_rate,
        converted_amount=converted_amount,
        status=TransactionStatus.PENDING.value
    )
    
    try:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Async-ish write to Redis for future idempotency checks
        if transaction_data.idempotency_key:
            txn_dict = {
                "id": str(transaction.id),
                "user_id": str(transaction.user_id),
                "amount": float(transaction.amount),
                "source_currency": transaction.source_currency,
                "target_currency": transaction.target_currency,
                "fx_rate": float(transaction.fx_rate),
                "converted_amount": float(transaction.converted_amount),
                "status": transaction.status,
                "idempotency_key": transaction.idempotency_key,
                "created_at": transaction.created_at.isoformat()
            }
            set_idempotent_transaction(transaction_data.idempotency_key, txn_dict)
            
        return transaction
    except IntegrityError:
        # Idempotency key race condition - fetch and return existing
        db.rollback()
        if transaction_data.idempotency_key:
            existing = get_transaction_by_idempotency_key(db, transaction_data.idempotency_key)
            if existing:
                return existing
        raise DuplicateIdempotencyKeyError("Duplicate idempotency key")


def get_transaction_by_id(db: Session, transaction_id: str) -> Optional[Transaction]:
    """
    Get a transaction by its ID.
    
    Args:
        db: Database session
        transaction_id: UUID of the transaction
        
    Returns:
        The Transaction model instance, or None if not found
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transaction_by_idempotency_key(db: Session, idempotency_key: str) -> Optional[Transaction]:
    """
    Get a transaction by its idempotency key.
    
    Args:
        db: Database session
        idempotency_key: The idempotency key
        
    Returns:
        The Transaction model instance, or None if not found
    """
    return db.query(Transaction).filter(
        Transaction.idempotency_key == idempotency_key
    ).first()


def get_transaction_or_raise(db: Session, transaction_id: str) -> Transaction:
    """
    Get a transaction by ID, raising an exception if not found.
    
    Args:
        db: Database session
        transaction_id: UUID of the transaction
        
    Returns:
        The Transaction model instance
        
    Raises:
        TransactionNotFoundError: If the transaction is not found
    """
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise TransactionNotFoundError(f"Transaction with ID '{transaction_id}' not found")
    return transaction


def get_transactions_by_user(
    db: Session, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> tuple[list[Transaction], int]:
    """
    Get all transactions for a user with pagination.
    
    Args:
        db: Database session
        user_id: UUID of the user
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (list of transactions, total count)
        
    Raises:
        UserNotFoundError: If the user doesn't exist
    """
    # Validate user exists
    get_user_or_raise(db, user_id)
    
    # Get total count
    total = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    
    # Get paginated results
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return transactions, total


def update_transaction_status(
    db: Session, 
    transaction_id: str, 
    new_status: SchemaTransactionStatus
) -> Transaction:
    """
    Update the status of a transaction.
    
    Valid transitions:
    - PENDING -> COMPLETED
    - PENDING -> FAILED
    
    Args:
        db: Database session
        transaction_id: UUID of the transaction
        new_status: The new status to set
        
    Returns:
        The updated Transaction model instance
        
    Raises:
        TransactionNotFoundError: If the transaction is not found
        InvalidStatusTransitionError: If the status transition is invalid
    """
    transaction = get_transaction_or_raise(db, transaction_id)
    
    current_status = TransactionStatus(transaction.status)
    
    # Define valid transitions
    valid_transitions = {
        TransactionStatus.PENDING: [TransactionStatus.COMPLETED, TransactionStatus.FAILED],
        TransactionStatus.COMPLETED: [],  # Terminal state
        TransactionStatus.FAILED: [],  # Terminal state
    }
    
    target_status = TransactionStatus(new_status.value)
    
    if target_status not in valid_transitions.get(current_status, []):
        raise InvalidStatusTransitionError(
            f"Cannot transition from {current_status.value} to {new_status.value}"
        )
    
    transaction.status = new_status.value
    db.commit()
    db.refresh(transaction)
    
    return transaction
