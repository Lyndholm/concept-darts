from datetime import date, datetime

from pydantic import BaseModel


class UserIn(BaseModel):
    first_name: str
    last_name: str
    additional_name: str | None = None
    date_of_birth: date
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    additional_name: str | None = None
    date_of_birth: date
    email: str
    created_at: datetime

    class Config:
        orm_mode = True
