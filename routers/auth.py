
import sqlite3

from fastapi import APIRouter, HTTPException

import database

from fastapi import Depends

from security import get_current_user_id


from models import UserRegister, UserResponse, UserLogin

from security import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserRegister):
    connection = sqlite3.connect(database.DATABASE_NAME)

    try:
        cursor = connection.cursor()

        email = str(user.email).strip().lower()

        # Check whether email already exists
        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        # Hash password, never store plaintext
        hashed_password = hash_password(user.password)

        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (user.name, email, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        return {
            "id": cursor.lastrowid,
            "name": user.name,
            "email": email
        }

    finally:
        connection.close()


@router.post("/login")
def login_user(user: UserLogin):
    connection = sqlite3.connect(
        database.DATABASE_NAME
    )

    try:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        email = str(user.email).strip().lower()

        cursor.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        found_user = cursor.fetchone()

        if found_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not verify_password(
            user.password,
            found_user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )


        access_token = create_access_token(
            found_user["id"]
        )

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": found_user["id"],
                "name": found_user["name"],
                "email": found_user["email"]
            }
        }


    finally:
        connection.close()


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    user_id: int = Depends(get_current_user_id)
):
    connection = sqlite3.connect(database.DATABASE_NAME)

    try:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid user credentials"
            )

        return dict(user)

    finally:
        connection.close()
