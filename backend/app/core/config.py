from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # MongoDB Configuration
    mongodb_url: str = Field("mongodb://localhost:27017", env="MONGODB_URL")
    
    # Email Configuration
    smtp_host: str = Field(..., env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str = Field(..., env="SMTP_USER")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    from_email: str = Field(..., env="FROM_EMAIL")
    from_name: str = Field("Restaurant Team", env="FROM_NAME")
    
    # Application Settings
    debug: bool = Field(False, env="DEBUG")
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:8080", "http://127.0.0.1:8080"], env="CORS_ORIGINS"
    )
    api_v1_str: str = Field("/api/v1", env="API_V1_STR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 