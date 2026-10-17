
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from pydantic import EmailStr



class Transaction(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    type: Literal["income", "expense"]

    @field_validator("title", "category")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must have at least 2 characters")

        return value


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str
