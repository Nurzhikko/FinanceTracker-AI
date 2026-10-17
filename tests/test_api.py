
import pytest
from fastapi.testclient import TestClient

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



def test_create_transaction(client):
    new_transaction = {
        "title": "Test Lunch",
        "amount": 2500,
        "category": "Food",
        "type": "expense"
    }

    # Create transaction
    response = client.post(
        "/transactions",
        json=new_transaction
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["transaction"]["title"] == "Test Lunch"
    assert data["transaction"]["amount"] == 2500

    # Verify transaction was saved
    response = client.get("/transactions")

    assert response.status_code == 200

    result = response.json()

    assert result["total"] == 1
    assert result["transactions"][0]["title"] == "Test Lunch"



def test_update_transaction(client):
    # Step 1: Create a transaction
    original = {
        "title": "Pizza",
        "amount": 3500,
        "category": "Food",
        "type": "expense"
    }

    create_response = client.post(
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

    update_response = client.put(
        f"/transactions/{transaction_id}",
        json=updated
    )

    assert update_response.status_code == 200
    assert update_response.json()["id"] == transaction_id

    # Step 3: Verify saved changes
    get_response = client.get("/transactions")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["total"] == 1

    saved = data["transactions"][0]

    assert saved["id"] == transaction_id
    assert saved["title"] == "Pizza and Coffee"
    assert saved["amount"] == 4500



def test_delete_transaction(client):
    # Step 1: Create a transaction
    transaction = {
        "title": "Taxi",
        "amount": 5000,
        "category": "Transport",
        "type": "expense"
    }

    create_response = client.post(
        "/transactions",
        json=transaction
    )

    assert create_response.status_code == 200

    transaction_id = create_response.json()["id"]

    # Step 2: Delete the transaction
    delete_response = client.delete(
        f"/transactions/{transaction_id}"
    )

    assert delete_response.status_code == 200

    assert delete_response.json() == {
        "message": "Transaction deleted successfully",
        "id": transaction_id
    }

    # Step 3: Verify transaction was deleted
    get_response = client.get("/transactions")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["total"] == 0
    assert data["transactions"] == []

    # Step 4: Verify deleting it again returns 404
    second_delete = client.delete(
        f"/transactions/{transaction_id}"
    )

    assert second_delete.status_code == 404
    assert second_delete.json()["detail"] == (
        "Transaction not found"
    )



def test_invalid_transaction_amount(client):
    transaction = {
        "title": "Invalid Expense",
        "amount": -500,
        "category": "Food",
        "type": "expense"
    }

    response = client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    # Invalid transaction must not be saved
    get_response = client.get("/transactions")

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0


def test_invalid_transaction_type(client):
    transaction = {
        "title": "Test Payment",
        "amount": 1000,
        "category": "Other",
        "type": "payment"
    }

    response = client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    get_response = client.get("/transactions")

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0



def test_financial_summary(client):
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

    response_income = client.post(
        "/transactions",
        json=income
    )

    response_expense = client.post(
        "/transactions",
        json=expense
    )

    assert response_income.status_code == 200
    assert response_expense.status_code == 200

    # Request financial summary
    response = client.get("/analytics/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 100000
    assert data["total_expenses"] == 25000
    assert data["balance"] == 75000


def test_category_analytics(client):
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
        response = client.post(
            "/transactions",
            json=transaction
        )
        assert response.status_code == 200

    # Request analytics
    response = client.get("/analytics/categories")

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


def test_empty_database_analytics(client):
    # Check financial summary
    response = client.get("/analytics/summary")

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 0,
        "total_expenses": 0,
        "balance": 0
    }

    # Check category analytics
    response = client.get("/analytics/categories")

    assert response.status_code == 200

    assert response.json() == {
        "categories": []
    }

    # Check transactions
    response = client.get("/transactions")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "transactions": []
    }


def test_update_nonexistent_transaction(client):
    transaction = {
        "title": "Unknown Transaction",
        "amount": 5000,
        "category": "Other",
        "type": "expense"
    }

    response = client.put(
        "/transactions/9999",
        json=transaction
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Transaction not found"
    }


def test_delete_nonexistent_transaction(client):
    response = client.delete(
        "/transactions/9999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Transaction not found"
    }


def test_zero_amount(client):
    transaction = {
        "title": "Coffee",
        "amount": 0,
        "category": "Food",
        "type": "expense"
    }

    response = client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422


def test_empty_transaction_title(client):
    transaction = {
        "title": "   ",
        "amount": 2500,
        "category": "Food",
        "type": "expense"
    }

    response = client.post(
        "/transactions",
        json=transaction
    )

    assert response.status_code == 422

    # Invalid data must not be saved
    result = client.get("/transactions")

    assert result.status_code == 200
    assert result.json()["total"] == 0
