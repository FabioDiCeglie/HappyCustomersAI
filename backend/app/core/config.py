from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    langchain_api_key: str = Field(..., env="LANGCHAIN_API_KEY")
    langchain_tracing_v2: bool = Field(True, env="LANGCHAIN_TRACING_V2")
    langchain_project: str = Field("feedback-ai", env="LANGCHAIN_PROJECT")
    
    # MongoDB Configuration
    mongodb_url: str = Field("mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field("email_support_ai", env="MONGODB_DATABASE")
    
    # Email Configuration
    smtp_host: str = Field(..., env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str = Field(..., env="SMTP_USER")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    from_email: str = Field(..., env="FROM_EMAIL")
    from_name: str = Field("Restaurant Team", env="FROM_NAME")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Application Settings
    debug: bool = Field(False, env="DEBUG")
    cors_origins: List[str] = Field(
        ["http://localhost:3000"], env="CORS_ORIGINS"
    )
    api_v1_str: str = Field("/api/v1", env="API_V1_STR")
    
    # Business Configuration
    restaurant_name: str = Field("Your Restaurant", env="RESTAURANT_NAME")
    restaurant_email: str = Field(..., env="RESTAURANT_EMAIL")
    restaurant_phone: str = Field("", env="RESTAURANT_PHONE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 