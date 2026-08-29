import os
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "LedgerGuard AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database & Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "data"))
    SAMPLE_DATA_DIR: str = os.path.abspath(os.path.join(DATA_DIR, "sample"))
    DB_PATH: str = os.path.join(BASE_DIR, "ledgerguard.db")
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"

    # CSV Upload limits
    MAX_CSV_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # Optional OpenAI Integration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

settings = Settings()
