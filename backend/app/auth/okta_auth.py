"""
Okta Authentication Module

Handles:
- ID Token validation
- WLP client assertion generation
- ID-JAG token exchange for XAA
"""

import jwt
import time
import uuid
import json
import httpx
from typing import Optional
from functools import lru_cache
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.models.schemas import UserInfo

security = HTTPBearer()


class OktaAuth:
    """Okta authentication and token exchange handler"""

    def __init__(self):
        self._jwks_cache: Optional[dict] = None
        self._jwks_cache_time: float = 0
        self._cache_ttl: int = 3600  # 1 hour

    async def get_jwks(self) -> dict:
        """Fetch and cache JWKS from Okta"""
        current_time = time.time()

        if self._jwks_cache and (current_time - self._jwks_cache_time) < self._cache_ttl:
            return self._jwks_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(settings.okta_jwks_uri)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = current_time

        return self._jwks_cache

    async def validate_id_token(self, token: str) -> UserInfo:
        """Validate an ID token from Okta"""
        try:
            # Get JWKS
            jwks = await self.get_jwks()

            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find the matching key
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

            if not rsa_key:
                raise HTTPException(status_code=401, detail="Invalid token: key not found")

            # Convert JWK to PEM for verification
            from jwt.algorithms import RSAAlgorithm
            public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))

            # Verify and decode
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.okta_client_id,
                issuer=settings.okta_issuer_url,
            )

            return UserInfo(
                sub=payload.get("sub"),
                email=payload.get("email", ""),
                name=payload.get("name"),
                given_name=payload.get("given_name"),
                family_name=payload.get("family_name"),
                groups=payload.get("groups", []),
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def generate_wlp_assertion(self, audience: Optional[str] = None) -> str:
        """
        Generate a JWT client assertion signed with the WLP private key.
        This proves the AI agent's identity to Okta.
        """
        if not settings.wlp_private_key:
            raise HTTPException(
                status_code=500, detail="WLP private key not configured"
            )

        now = int(time.time())
        aud = audience or f"https://{settings.okta_domain}/oauth2/v1/token"

        payload = {
            "iss": settings.wlp_client_id,
            "sub": settings.wlp_client_id,
            "aud": aud,
            "iat": now,
            "exp": now + 300,  # 5 minutes
            "jti": str(uuid.uuid4()),
        }

        # Parse private key from JWK
        private_key_jwk = json.loads(settings.wlp_private_key)
        from jwt.algorithms import RSAAlgorithm
        private_key = RSAAlgorithm.from_jwk(json.dumps(private_key_jwk))

        return jwt.encode(payload, private_key, algorithm="RS256")

    async def exchange_for_id_jag(self, id_token: str) -> str:
        """
        Exchange user's ID token for an ID-JAG at the Org Authorization Server.

        Step 1 of the ID-JAG flow:
        - Input: User's ID token
        - Output: ID-JAG (Identity Assertion JWT with `act` claim = WLP)
        """
        client_assertion = self.generate_wlp_assertion()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{settings.okta_domain}/oauth2/v1/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": id_token,
                    "client_id": settings.okta_client_id,
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion,
                    "scope": "openid profile email",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error = response.json()
                raise HTTPException(
                    status_code=401,
                    detail=f"ID-JAG exchange failed: {error.get('error_description', error.get('error'))}",
                )

            data = response.json()
            return data.get("id_token")  # This is the ID-JAG

    async def exchange_id_jag_for_token(
        self,
        id_jag: str,
        auth_server_id: str,
        scopes: list[str],
    ) -> dict:
        """
        Exchange ID-JAG for a scoped access token at a Custom Authorization Server.

        Step 2 of the ID-JAG flow:
        - Input: ID-JAG from Step 1
        - Output: Scoped access token for the target resource
        """
        client_assertion = self.generate_wlp_assertion(
            audience=f"https://{settings.okta_domain}/oauth2/{auth_server_id}/v1/token"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{settings.okta_domain}/oauth2/{auth_server_id}/v1/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "subject_token": id_jag,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
                    "client_id": settings.okta_client_id,
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion,
                    "scope": " ".join(scopes),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error = response.json()
                # Don't raise - return access denied info
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
                "scope": data.get("scope"),
            }


# Singleton instance
okta_auth = OktaAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserInfo:
    """Dependency to get the current authenticated user from ID token"""
    return await okta_auth.validate_id_token(credentials.credentials)


async def get_id_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Dependency to get the raw ID token"""
    return credentials.credentials
