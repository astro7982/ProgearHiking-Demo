"""
Auth0 Token Vault Integration

Handles:
- Token exchange from Okta to Auth0
- Retrieving provider tokens (Salesforce) from Token Vault
- Managing user linked accounts
"""

import httpx
from typing import Optional
from fastapi import HTTPException

from app.core.config import settings
from app.auth.okta_auth import okta_auth


class TokenVault:
    """Auth0 Token Vault handler for external service access"""

    def __init__(self):
        self._management_token: Optional[str] = None
        self._token_expiry: float = 0

    async def get_management_token(self) -> str:
        """Get Auth0 Management API token"""
        import time

        if self._management_token and time.time() < self._token_expiry:
            return self._management_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{settings.auth0_domain}/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": settings.auth0_client_id,
                    "client_secret": settings.auth0_client_secret,
                    "audience": f"https://{settings.auth0_domain}/api/v2/",
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get Auth0 management token",
                )

            data = response.json()
            self._management_token = data["access_token"]
            self._token_expiry = time.time() + data.get("expires_in", 86400) - 60

            return self._management_token

    async def exchange_okta_token_for_vault(self, id_jag: str) -> dict:
        """
        Exchange Okta ID-JAG for Auth0 Token Vault access.

        This allows the agent to access Token Vault while maintaining
        the WLP identity in the `act` claim for audit purposes.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{settings.auth0_domain}/oauth/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "subject_token": id_jag,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
                    "client_id": settings.auth0_client_id,
                    "client_secret": settings.auth0_client_secret,
                    "audience": f"https://{settings.auth0_domain}/api/v2/",
                    "scope": "read:users read:user_idp_tokens",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error = response.json()
                return {
                    "success": False,
                    "error": error.get("error"),
                    "error_description": error.get("error_description"),
                }

            data = response.json()
            return {
                "success": True,
                "access_token": data.get("access_token"),
                "token_type": data.get("token_type", "Bearer"),
                "expires_in": data.get("expires_in"),
            }

    async def get_salesforce_token(
        self,
        auth0_user_id: str,
        vault_token: Optional[str] = None,
    ) -> dict:
        """
        Get Salesforce access token from Token Vault for a specific user.

        The token is retrieved from the user's linked Salesforce identity.
        """
        token = vault_token or await self.get_management_token()

        async with httpx.AsyncClient() as client:
            # Get user's linked identities
            response = await client.get(
                f"https://{settings.auth0_domain}/api/v2/users/{auth0_user_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"fields": "identities", "include_fields": "true"},
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "error_description": "Could not find user in Auth0",
                }

            user_data = response.json()
            identities = user_data.get("identities", [])

            # Find Salesforce identity
            salesforce_identity = None
            for identity in identities:
                if identity.get("provider") == settings.salesforce_connection_name:
                    salesforce_identity = identity
                    break

            if not salesforce_identity:
                return {
                    "success": False,
                    "error": "salesforce_not_connected",
                    "error_description": "User has not connected their Salesforce account",
                }

            # Get the access token
            access_token = salesforce_identity.get("access_token")
            refresh_token = salesforce_identity.get("refresh_token")

            if not access_token:
                return {
                    "success": False,
                    "error": "no_token",
                    "error_description": "No Salesforce token available",
                }

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "instance_url": settings.salesforce_instance_url,
            }

    async def check_salesforce_connection(self, auth0_user_id: str) -> bool:
        """Check if user has connected their Salesforce account"""
        result = await self.get_salesforce_token(auth0_user_id)
        return result.get("success", False)

    async def get_connection_auth_url(
        self,
        connection: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """Generate authorization URL for connecting an external account"""
        import urllib.parse

        params = {
            "client_id": settings.auth0_client_id,
            "response_type": "code",
            "connection": connection,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email offline_access",
        }

        if state:
            params["state"] = state

        query = urllib.parse.urlencode(params)
        return f"https://{settings.auth0_domain}/authorize?{query}"

    async def get_user_id_from_okta_sub(self, okta_sub: str) -> Optional[str]:
        """
        Find Auth0 user ID from Okta subject.

        Users are federated from Okta to Auth0, so we need to look up
        the Auth0 user ID based on the Okta identity.
        """
        token = await self.get_management_token()

        async with httpx.AsyncClient() as client:
            # Search for user by Okta identity
            response = await client.get(
                f"https://{settings.auth0_domain}/api/v2/users",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "q": f'identities.user_id:"{okta_sub}"',
                    "search_engine": "v3",
                },
            )

            if response.status_code != 200:
                return None

            users = response.json()
            if users and len(users) > 0:
                return users[0].get("user_id")

            return None


# Singleton instance
token_vault = TokenVault()
