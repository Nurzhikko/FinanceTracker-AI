
import sqlite3

from fastapi import APIRouter, HTTPException

import database
from models import Transaction


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post("")
def create_transaction(transaction: Transaction):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO transactions
            (title, amount, category, type)
            VALUES (?, ?, ?, ?)
            """,
            (
                transaction.title,
                transaction.amount,
                transaction.category,
                transaction.type
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
def get_transactions():
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM transactions ORDER BY id DESC"
        )

        rows = cursor.fetchall()

        transactions = [
            dict(row) for row in rows
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
    transaction: Transaction
):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE transactions
            SET title = ?,
                amount = ?,
                category = ?,
                type = ?
            WHERE id = ?
            """,
            (
                transaction.title,
                transaction.amount,
                transaction.category,
                transaction.type,
                transaction_id
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
def delete_transaction(transaction_id: int):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
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
