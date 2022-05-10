from datetime import date, datetime

from pydantic import BaseModel, EmailStr, validator


class BaseUser(BaseModel):
    first_name: str
    last_name: str
    additional_name: str | None = None
    date_of_birth: date


class UserWithPassword(BaseModel):
    password: str
    
    @validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError('password should be at least 8 characters long')
        return value


class UserIn(UserWithPassword, BaseUser):
    email: EmailStr


class UserOut(BaseUser):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True


class UserOutPublic(BaseUser):
    id: int

    class Config:
        orm_mode = True


class UserUpdate(UserWithPassword, BaseModel):
    first_name: str | None
    last_name: str | None
    additional_name: str | None
    date_of_birth: date | None
    password: str | None
