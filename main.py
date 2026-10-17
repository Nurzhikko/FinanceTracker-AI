
from fastapi import FastAPI

from database import DATABASE_NAME


app = FastAPI(
    title="FinanceTracker AI",
    description="Personal finance management API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to FinanceTracker AI!",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


from pydantic import BaseModel, Field
from typing import Literal

class Transaction(BaseModel):
    title:str
    amount: float = Field(gt=0)
    category: str
    type: Literal["income", "expense"]


@app.post("/transactions")
def create_transaction(transaction: Transaction):
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)
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
    connection.close()

    return{
        "message": "Transaction created successfully",
        "id": transaction_id,
        "transaction": transaction
    }



@app.get("/transactions")
def get_transactions():
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM transactions ORDER BY id DESC"
    )

    rows = cursor.fetchall()

    transactions = [
        dict(row) for row in rows
    ]

    connection.close()

    return {
        "total": len(transactions),
        "transactions": transactions
    }


from fastapi import HTTPException


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)

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



@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: Transaction
):
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)

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


@app.get("/analytics/summary")
def get_financial_summary():
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT 
                COALESCE(SUM(
                CASE WHEN type = 'income'
                THEN amount ELSE 0 END
                ), 0),
                COALESCE(SUM(
                CASE WHEN type = 'expense'
                THEN amount ELSE 0 END
                ), 0)
            FROM transactions
        """)

        income, expenses = cursor.fetchone()

        return{
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "balance":round(income-expenses, 2)
        }
    finally:
        connection.close()


@app.get("/analytics/categories")
def get_category_analytics():
    import sqlite3

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                category,
                COUNT(*) AS transaction_count,
                ROUND(SUM(amount), 2) AS total
            FROM transactions
            WHERE type = 'expense'
            GROUP BY category
            ORDER BY total DESC
        """)

        rows = cursor.fetchall()

        categories = []

        for row in rows:
            categories.append({
                "category": row[0],
                "transaction_count": row[1],
                "total": row[2]
            })

        return {
            "categories": categories
        }

    finally:
        connection.close()



from fastapi.staticfiles import StaticFiles

app.mount(
    "/dashboard",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)
