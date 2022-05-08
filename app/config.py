from pydantic import BaseSettings


class Config(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str


config = Config(_env_file= '.env', _env_file_encoding = 'utf-8')
