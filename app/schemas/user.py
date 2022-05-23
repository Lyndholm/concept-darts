from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator

from ..config import config


class BaseUser(BaseModel):
    username: str
    first_name: str
    last_name: str
    additional_name: str | None
    avatar_image: str | None

    class Config:
        orm_mode = True


class BaseUserData(BaseUser):
    date_of_birth: date | None
    phone_number: str | None

    @validator('phone_number')
    def validate_phone_number(cls, value):
        if value is None:
            return value
        if len(value) > 15:
            raise ValueError('phone number should not exceed 15 digits')
        return value


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
    additional_name: str | None
    date_of_birth: date | None
    password: str | None
    avatar_image: str | None


class UserIn(UserWithPassword, BaseUserData):
    email: EmailStr


class UserOutBase(BaseUser):
    id: UUID

    @validator('avatar_image')
    def format_image_url(cls, value) -> str:
        if value is None:
            return value
        return config.STATIC_STORAGE_BASE_URL + value if config.STATIC_STORAGE_BASE_URL not in value else value


class UserCreated(UserOutBase, BaseUserData):
    ...


class UserOutPublic(UserOutBase):
    ...


# Import here to avoid circular import
from .world import WorldOwnedByUser
from .location import LocationOwnedByUser

class UserProfile(UserOutPublic):
    worlds: list[WorldOwnedByUser] = []
    locations: list[LocationOwnedByUser] = []


class UserOutPrivate(UserProfile):
    email: EmailStr


class UserUpdatedOut(UserOutPublic):
    email: EmailStr
