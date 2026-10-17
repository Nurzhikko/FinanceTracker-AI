

import sqlite3
import os

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "finance.db"
)



def create_database():
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            type TEXT NOT NULL
                CHECK(type IN ('income', 'expense'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check existing transaction columns
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add user_id to existing database
    if "user_id" not in columns:
        cursor.execute("""
            ALTER TABLE transactions
            ADD COLUMN user_id INTEGER
            REFERENCES users(id)
        """)

    # Index for faster filtering by user
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_transactions_user_id
        ON transactions(user_id)
    """)



    connection.commit()
    connection.close()

    print("Database created successfully!")


if __name__ == "__main__":
    create_database()
