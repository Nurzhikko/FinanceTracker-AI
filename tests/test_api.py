
import pytest
from fastapi.testclient import TestClient

from security import create_access_token

import database
import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create an isolated temporary database
    test_db = tmp_path / "finance_test.db"

    # Redirect API database connections
    monkeypatch.setattr(
        main,
        "DATABASE_NAME",
        str(test_db)
    )

    # Initialize the test database
    monkeypatch.setattr(
        database,
        "DATABASE_NAME",
        str(test_db)
    )

    database.create_database()

    # Create a FastAPI test client
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }



def test_create_transaction(auth_client):
    new_transaction = {
        "title": "Test Lunch",
        "amount": 2500,
        "category": "Food",
        "type": "expense"
    }

    # Create transaction
    response = auth_client.post(
        "/transactions",
        json=new_transaction
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["transaction"]["title"] == "Test Lunch"
    assert data["transaction"]["amount"] == 2500

    # Verify transaction was saved
    response = auth_client.get("/transactions")

    assert response.status_code == 200

    result = response.json()

    assert result["total"] == 1
    assert result["transactions"][0]["title"] == "Test Lunch"



def test_update_transaction(auth_client):
    # Step 1: Create a transaction
    original = {
        "title": "Pizza",
        "amount": 3500,
        "category": "Food",
        "type": "expense"
    }

    create_response = auth_client.post(
        "/transactions",
        json=original
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    # Step 2: Update the transaction
    updated = {
        "title": "Pizza and Coffee",
        "amount": 4500,
        "category": "Food",
        "type": "expense"
    }

    update_response = auth_client.put(
        f"/transactions/{transaction_id}",
        json=updated
    )

    assert update_response.status_code == 200
    assert update_response.json()["id"] == transaction_id

    # Step 3: Verify saved changes
    get_response = auth_client.get("/transactions")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["total"] == 1

    saved = data["transactions"][0]

    assert saved["id"] == transaction_id
    assert saved["title"] == "Pizza and Coffee"
    assert saved["amount"] == 4500



def test_delete_transaction(auth_client):
    # Step 1: Create a transaction
    transaction = {
        "title": "Taxi",
        "amount": 5000,
        "category": "Transport",
        "type": "expense"
    }

    create_response = auth_client.post(
        "/transactions",
        json=transaction
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    # Step 2: Delete the transaction
    delete_response = auth_client.delete(
        f"/transactions/{transaction_id}"
    )

    assert delete_response.status_code == 200

    assert delete_response.json() == {
        "message": "Transaction deleted successfully",
        "id": transaction_id
    }

    # Step 3: Verify transaction was deleted
    get_response = auth_client.get("/transactions")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["total"] == 0
    assert data["transactions"] == []

    # Step 4: Verify deleting it again returns 404
    second_delete = auth_client.delete(
        f"/transactions/{transaction_id}"
    )

    assert second_delete.status_code == 404
    assert second_delete.json()["detail"] == (
        "Transaction not found"
    )



def test_invalid_transaction_amount(auth_client):
    transaction = {
        "title": "Invalid Expense",
        "amount": -500,
        "category": "Food",
        "type": "expense"
    }

    response = auth_client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    # Invalid transaction must not be saved
    get_response = auth_client.get("/transactions")

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0


def test_invalid_transaction_type(auth_client):
    transaction = {
        "title": "Test Payment",
        "amount": 1000,
        "category": "Other",
        "type": "payment"
    }

    response = auth_client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    get_response = auth_client.get("/transactions")

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0



def test_financial_summary(auth_client):
    # Create income
    income = {
        "title": "Salary",
        "amount": 100000,
        "category": "Salary",
        "type": "income"
    }

    # Create expense
    expense = {
        "title": "Food",
        "amount": 25000,
        "category": "Food",
        "type": "expense"
    }

    response_income = auth_client.post(
        "/transactions",
        json=income
    )

    response_expense = auth_client.post(
        "/transactions",
        json=expense
    )

    assert response_income.status_code == 200
    assert response_expense.status_code == 200

    # Request financial summary
    response = auth_client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 100000
    assert data["total_expenses"] == 25000
    assert data["balance"] == 75000


def test_category_analytics(auth_client):
    transactions = [
        {
            "title": "Pizza",
            "amount": 3500,
            "category": "Food",
            "type": "expense"
        },
        {
            "title": "Coffee",
            "amount": 1500,
            "category": "Food",
            "type": "expense"
        },
        {
            "title": "Taxi",
            "amount": 5000,
            "category": "Transport",
            "type": "expense"
        }
    ]

    for transaction in transactions:
        response = auth_client.post(
            "/transactions",
            json=transaction
        )
        assert response.status_code == 200

    # Request analytics
    response = auth_client.get("/analytics/categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data["categories"]) == 2

    categories = {
        item["category"]: item
        for item in data["categories"]
    }

    assert categories["Food"]["total"] == 5000
    assert categories["Food"]["transaction_count"] == 2

    assert categories["Transport"]["total"] == 5000
    assert categories["Transport"]["transaction_count"] == 1


def test_empty_database_analytics(auth_client):
    # Check financial summary
    response = auth_client.get("/analytics/summary")

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 0,
        "total_expenses": 0,
        "balance": 0
    }

    # Check category analytics
    response = auth_client.get("/analytics/categories")

    assert response.status_code == 200

    assert response.json() == {
        "categories": []
    }

    # Check transactions
    response = auth_client.get("/transactions")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "transactions": []
    }


def test_update_nonexistent_transaction(auth_client):
    transaction = {
        "title": "Unknown Transaction",
        "amount": 5000,
        "category": "Other",
        "type": "expense"
    }

    response = auth_client.put(
        "/transactions/9999",
        json=transaction
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Transaction not found"
    }


def test_delete_nonexistent_transaction(auth_client):
    response = auth_client.delete(
        "/transactions/9999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Transaction not found"
    }


def test_zero_amount(auth_client):
    transaction = {
        "title": "Coffee",
        "amount": 0,
        "category": "Food",
        "type": "expense"
    }

    response = auth_client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422


def test_empty_transaction_title(auth_client):
    transaction = {
        "title": "   ",
        "amount": 2500,
        "category": "Food",
        "type": "expense"
    }

    response = auth_client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    # Invalid data must not be saved
    result = auth_client.get("/transactions")

    assert result.status_code == 200
    assert result.json()["total"] == 0


def test_register_user(client):
    user = {
        "name": "Test User",
        "email": "newuser@example.com",
        "password": "TestPassword123!"
    }

    response = client.post(
        "/auth/register",
        json=user
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Test User"
    assert data["email"] == "newuser@example.com"

    # Password must never be returned
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email(client):
    user = {
        "name": "Test User",
        "email": "duplicate@example.com",
        "password": "TestPassword123!"
    }

    first_response = client.post(
        "/auth/register",
        json=user
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=user
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "Email already registered"
    }

def test_transactions_require_authentication(client):
    response = client.get("/transactions")
    assert response.status_code == 401


def test_create_transaction_requires_authentication(client):
    response = client.post(
        "/transactions",
        json={
            "title": "Coffee",
            "amount": 1500,
            "category": "Food",
            "type": "expense"
        }
    )
    assert response.status_code == 401


def test_analytics_require_authentication(client):
    response = client.get("/analytics/summary")
    assert response.status_code == 401

    response = client.get("/analytics/categories")
    assert response.status_code == 401


@pytest.fixture
def auth_client(client, monkeypatch):
    # Test-only JWT key
    monkeypatch.setattr(
        "security.JWT_SECRET_KEY",
        "test-secret-key-for-pytest-only-1234567890"
    )

    # Create test user
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "auth-test@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    # Generate JWT
    token = create_access_token(user_id)

    # Automatically attach token to requests
    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return client


def test_authenticated_client(auth_client):
    response = auth_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "auth-test@example.com"
