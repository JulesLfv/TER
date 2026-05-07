import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ter")
    sample_step_m: int = int(os.getenv("SAMPLE_STEP_M", "200"))
    segment_length_m: int = int(os.getenv("SEGMENT_LENGTH_M", "500"))
    radius_4g_m: int = int(os.getenv("RADIUS_4G_M", "3000"))
    radius_5g_m: int = int(os.getenv("RADIUS_5G_M", "1500"))


settings = Settings()
