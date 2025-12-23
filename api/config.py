import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql://airflow:airflow@postgres/olap_database"

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "reports-realm"
    keycloak_client_id: str = "reports-frontend"
    keycloak_client_secret: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()