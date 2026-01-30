from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "ProGear Hiking API"
    debug: bool = False
    api_prefix: str = "/api"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "https://*.vercel.app"]

    # Okta Configuration
    okta_domain: str = "qa-aiagentsproducttc1.trexcloud.com"
    okta_client_id: str = "0oa8zcwqfrsi1Mi5Z0g7"
    okta_client_secret: str = ""
    okta_issuer: str = ""

    # Workload Principal (WLP)
    wlp_client_id: str = "wlp8zcxwhpsu387C20g7"
    wlp_private_key: str = ""  # JSON string of JWK

    # Inventory Auth Server (Okta Custom AS)
    inventory_auth_server_id: str = ""
    inventory_scopes: list[str] = ["inventory:read", "inventory:write", "inventory:alert"]

    # Auth0 Configuration (Token Vault)
    auth0_domain: str = "dev-4i2mhp2tnupmhbik.us.auth0.com"
    auth0_client_id: str = ""
    auth0_client_secret: str = ""
    auth0_audience: str = ""

    # Salesforce
    salesforce_instance_url: str = "https://orgfarm-3592c48138-dev-ed.develop.my.salesforce.com"
    salesforce_connection_name: str = "salesforce"

    # Azure AI Foundry
    azure_foundry_endpoint: str = ""
    azure_foundry_api_key: str = ""
    azure_foundry_deployment: str = "gpt-4"

    @property
    def okta_issuer_url(self) -> str:
        if self.okta_issuer:
            return self.okta_issuer
        return f"https://{self.okta_domain}"

    @property
    def okta_jwks_uri(self) -> str:
        return f"{self.okta_issuer_url}/oauth2/v1/keys"

    @property
    def auth0_issuer_url(self) -> str:
        return f"https://{self.auth0_domain}/"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
