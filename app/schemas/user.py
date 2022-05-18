from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator


class BaseUser(BaseModel):
    username: str
    first_name: str
    last_name: str
    avatar_image: str | None

    class Config:
        orm_mode = True


class BaseUserData(BaseUser):
    date_of_birth: date


class UserWithPassword(BaseModel):
    password: str
    
    @validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('password should be at least 8 characters long')
        return value


class UserUpdate(UserWithPassword):
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    password: str | None
    avatar_image: str | None


class UserIn(UserWithPassword, BaseUserData):
    email: EmailStr


class UserOutBase(BaseUser):
    id: UUID


class UserOutPublic(UserOutBase):
    ...


class UserOutPrivate(UserOutPublic, BaseUser):
    email: EmailStr
