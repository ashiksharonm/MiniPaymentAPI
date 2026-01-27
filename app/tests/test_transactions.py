"""
Tests for Transaction API endpoints and FX conversion.
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.fx_rates import FX_RATES, convert_currency, get_fx_rate


class TestFXConversion:
    """Tests for FX conversion logic."""
    
    def test_usd_to_inr_conversion(self):
        """Test USD to INR conversion with correct rate."""
        amount = Decimal("100")
        converted, rate = convert_currency(amount, "USD", "INR")
        
        assert rate == Decimal("83.00")
        assert converted == Decimal("8300.00")
    
    def test_usd_to_eur_conversion(self):
        """Test USD to EUR conversion with correct rate."""
        amount = Decimal("100")
        converted, rate = convert_currency(amount, "USD", "EUR")
        
        assert rate == Decimal("0.92")
        assert converted == Decimal("92.00")
    
    def test_eur_to_usd_conversion(self):
        """Test EUR to USD conversion with correct rate."""
        amount = Decimal("100")
        converted, rate = convert_currency(amount, "EUR", "USD")
        
        assert rate == Decimal("1.08")
        assert converted == Decimal("108.00")
    
    def test_same_currency_conversion(self):
        """Test same currency conversion returns 1:1 rate."""
        amount = Decimal("100")
        converted, rate = convert_currency(amount, "USD", "USD")
        
        assert rate == Decimal("1.00")
        assert converted == Decimal("100.00")
    
    def test_unsupported_currency(self):
        """Test that unsupported currencies return None."""
        rate = get_fx_rate("XYZ", "USD")
        assert rate is None
        
        converted, rate = convert_currency(Decimal("100"), "XYZ", "USD")
        assert converted is None
        assert rate is None
    
    def test_conversion_rounding(self):
        """Test that conversion results are rounded to 2 decimal places."""
        # Use an amount that would result in more than 2 decimal places
        amount = Decimal("33.33")
        converted, rate = convert_currency(amount, "USD", "EUR")
        
        # 33.33 * 0.92 = 30.6636, should round to 30.66
        assert converted == Decimal("30.66")


class TestCreateTransaction:
    """Tests for transaction creation endpoint."""
    
    def test_create_transaction_success(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test successful transaction creation with FX conversion."""
        # Create user first
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        # Create transaction
        transaction_data = {**sample_transaction_data, "user_id": user_id}
        response = client.post("/transactions", json=transaction_data, headers=api_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == user_id
        assert data["amount"] == "100.0000"
        assert data["source_currency"] == "USD"
        assert data["target_currency"] == "INR"
        assert data["fx_rate"] == "83.00000000"
        assert data["converted_amount"] == "8300.0000"
        assert data["status"] == "PENDING"
    
    def test_create_transaction_with_idempotency_key(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test that idempotency key prevents duplicate transactions."""
        # Create user
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        # Create first transaction with idempotency key
        transaction_data = {
            **sample_transaction_data, 
            "user_id": user_id,
            "idempotency_key": "test-key-123"
        }
        response1 = client.post("/transactions", json=transaction_data, headers=api_headers)
        assert response1.status_code == 201
        transaction_id = response1.json()["id"]
        
        # Attempt to create second transaction with same idempotency key
        response2 = client.post("/transactions", json=transaction_data, headers=api_headers)
        
        # Should return the existing transaction, not create a new one
        assert response2.status_code == 201
        assert response2.json()["id"] == transaction_id
    
    def test_create_transaction_user_not_found(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_transaction_data: dict
    ):
        """Test that transaction creation fails for non-existent user."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        transaction_data = {**sample_transaction_data, "user_id": fake_user_id}
        
        response = client.post("/transactions", json=transaction_data, headers=api_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_transaction_invalid_currency(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict
    ):
        """Test that invalid currencies are rejected."""
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {
            "user_id": user_id,
            "amount": "100.00",
            "source_currency": "XYZ",  # Invalid
            "target_currency": "INR"
        }
        
        response = client.post("/transactions", json=transaction_data, headers=api_headers)
        
        assert response.status_code == 422
    
    def test_create_transaction_negative_amount(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict
    ):
        """Test that negative amounts are rejected."""
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {
            "user_id": user_id,
            "amount": "-100.00",
            "source_currency": "USD",
            "target_currency": "INR"
        }
        
        response = client.post("/transactions", json=transaction_data, headers=api_headers)
        
        assert response.status_code == 422


class TestGetTransaction:
    """Tests for transaction retrieval endpoint."""
    
    def test_get_transaction_success(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test successful transaction retrieval."""
        # Create user and transaction
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {**sample_transaction_data, "user_id": user_id}
        create_response = client.post("/transactions", json=transaction_data, headers=api_headers)
        transaction_id = create_response.json()["id"]
        
        # Get the transaction
        response = client.get(f"/transactions/{transaction_id}", headers=api_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == transaction_id
    
    def test_get_transaction_not_found(
        self, 
        client: TestClient, 
        api_headers: dict
    ):
        """Test that non-existent transaction returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/transactions/{fake_id}", headers=api_headers)
        
        assert response.status_code == 404


class TestListUserTransactions:
    """Tests for listing user transactions."""
    
    def test_list_user_transactions(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test listing all transactions for a user."""
        # Create user
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        # Create multiple transactions
        for i in range(3):
            transaction_data = {
                **sample_transaction_data, 
                "user_id": user_id,
                "idempotency_key": f"key-{i}"
            }
            client.post("/transactions", json=transaction_data, headers=api_headers)
        
        # List transactions
        response = client.get(f"/users/{user_id}/transactions", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["transactions"]) == 3
    
    def test_list_user_transactions_pagination(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test pagination of user transactions."""
        # Create user
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        # Create 5 transactions
        for i in range(5):
            transaction_data = {
                **sample_transaction_data, 
                "user_id": user_id,
                "idempotency_key": f"key-{i}"
            }
            client.post("/transactions", json=transaction_data, headers=api_headers)
        
        # List with limit
        response = client.get(
            f"/users/{user_id}/transactions?skip=0&limit=2", 
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["transactions"]) == 2


class TestUpdateTransactionStatus:
    """Tests for transaction status updates."""
    
    def test_update_status_to_completed(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test updating transaction status from PENDING to COMPLETED."""
        # Create user and transaction
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {**sample_transaction_data, "user_id": user_id}
        create_response = client.post("/transactions", json=transaction_data, headers=api_headers)
        transaction_id = create_response.json()["id"]
        
        # Update status
        response = client.patch(
            f"/transactions/{transaction_id}/status",
            json={"status": "COMPLETED"},
            headers=api_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"
    
    def test_update_status_to_failed(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test updating transaction status from PENDING to FAILED."""
        # Create user and transaction
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {**sample_transaction_data, "user_id": user_id}
        create_response = client.post("/transactions", json=transaction_data, headers=api_headers)
        transaction_id = create_response.json()["id"]
        
        # Update status
        response = client.patch(
            f"/transactions/{transaction_id}/status",
            json={"status": "FAILED"},
            headers=api_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "FAILED"
    
    def test_invalid_status_transition(
        self, 
        client: TestClient, 
        api_headers: dict, 
        sample_user_data: dict,
        sample_transaction_data: dict
    ):
        """Test that invalid status transitions are rejected."""
        # Create user and transaction
        user_response = client.post("/users", json=sample_user_data, headers=api_headers)
        user_id = user_response.json()["id"]
        
        transaction_data = {**sample_transaction_data, "user_id": user_id}
        create_response = client.post("/transactions", json=transaction_data, headers=api_headers)
        transaction_id = create_response.json()["id"]
        
        # First, complete the transaction
        client.patch(
            f"/transactions/{transaction_id}/status",
            json={"status": "COMPLETED"},
            headers=api_headers
        )
        
        # Try to change COMPLETED back to PENDING (invalid)
        response = client.patch(
            f"/transactions/{transaction_id}/status",
            json={"status": "PENDING"},
            headers=api_headers
        )
        
        assert response.status_code == 400
        assert "Cannot transition" in response.json()["detail"]
