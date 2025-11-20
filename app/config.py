"""Configurações da aplicação."""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


# Caminho para o arquivo .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente."""
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "whatsapp_middleware"
    
    # WhatsApp Cloud API
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""
    
    # Aplicação
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignora variáveis extras no .env


settings = Settings()

