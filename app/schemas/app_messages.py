from pydantic import BaseModel


class ResponseError(BaseModel):
    status: int
    error: str
