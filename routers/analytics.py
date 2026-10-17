
import sqlite3

from fastapi import APIRouter

import database


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/summary")
def get_financial_summary():
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

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

        return {
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "balance": round(income - expenses, 2)
        }

    finally:
        connection.close()


@router.get("/categories")
def get_category_analytics():
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

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
