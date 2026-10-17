
import sqlite3

from fastapi import APIRouter, HTTPException, Depends
from security import get_current_user_id


import database
from models import Transaction


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)



@router.post("")
def create_transaction(
    transaction: Transaction,
    user_id: int = Depends(get_current_user_id)
):
    connection = sqlite3.connect(database.DATABASE_NAME)

    try:
        cursor = connection.cursor()

        # Check that the token owner still exists
        cursor.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid user credentials"
            )

        cursor.execute(
            """
            INSERT INTO transactions
            (title, amount, category, type, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                transaction.title,
                transaction.amount,
                transaction.category,
                transaction.type,
                user_id
            )
        )

        connection.commit()
        transaction_id = cursor.lastrowid

        return {
            "message": "Transaction created successfully",
            "id": transaction_id,
            "transaction": transaction
        }

    finally:
        connection.close()





@router.get("")
def get_transactions(
    user_id: int = Depends(get_current_user_id)
):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        # Check that the user still exists
        cursor.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid user credentials"
            )

        # Retrieve only the user's transactions
        cursor.execute(
            """
            SELECT id, title, amount, category, type
            FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        )

        transactions = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "total": len(transactions),
            "transactions": transactions
        }

    finally:
        connection.close()





@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: Transaction,
    user_id: int = Depends(get_current_user_id)
):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        cursor = connection.cursor()

        # Update only the current user's transaction
        cursor.execute(
            """
            UPDATE transactions
            SET title = ?,
                amount = ?,
                category = ?,
                type = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                transaction.title,
                transaction.amount,
                transaction.category,
                transaction.type,
                transaction_id,
                user_id
            )
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        connection.commit()

        return {
            "message": "Transaction updated successfully",
            "id": transaction_id,
            "transaction": transaction
        }

    finally:
        connection.close()



@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id)
):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM transactions
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        connection.commit()

        return {
            "message": "Transaction deleted successfully",
            "id": transaction_id
        }

    finally:
        connection.close()
