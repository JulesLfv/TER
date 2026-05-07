from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TER Coverage API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ter"


settings = Settings()
