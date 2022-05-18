from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator


class BaseUser(BaseModel):
    username: str
    first_name: str
    last_name: str
    date_of_birth: date
    avatar_image: str | None


class UserWithPassword(BaseModel):
    password: str
    
    @validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('password should be at least 8 characters long')
        return value


class UserIn(UserWithPassword, BaseUser):
    email: EmailStr


class UserOutPublic(BaseUser):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class UserOutPrivate(UserOutPublic, BaseUser):
    email: EmailStr

    class Config:
        orm_mode = True


class UserUpdate(UserWithPassword, BaseModel):
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    password: str | None
    avatar_image: str | None
