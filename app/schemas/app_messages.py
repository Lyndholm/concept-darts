from pydantic import BaseModel


class ResponceError(BaseModel):
    status: int
    error: str
