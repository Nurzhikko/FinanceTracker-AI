
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
