from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, validator

from app.config import config


class BaseFile(BaseModel):
    filename: str

    class Config:
        orm_mode = True


class FileOut(BaseFile):
    author_id: UUID
    uploaded_at: datetime


class FileOutWithStorageUrl(FileOut):
    @validator('filename')
    def format_image_url(cls, value) -> str:
        return config.STATIC_STORAGE_BASE_URL + value if config.STATIC_STORAGE_BASE_URL not in value else value
