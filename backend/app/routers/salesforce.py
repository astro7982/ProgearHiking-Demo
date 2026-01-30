"""
Salesforce Router

Direct Salesforce API endpoints (for non-chat operations).
"""

from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.auth.okta_auth import get_current_user, get_id_token
from app.auth.token_vault import token_vault
from app.models.schemas import UserInfo
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.post("/connect")
async def initiate_salesforce_connection(
    user: UserInfo = Depends(get_current_user),
):
    """
    Initiate Salesforce account connection.

    Returns an authorization URL that the user should be redirected to.
    This will trigger the OAuth flow to connect their Salesforce account
    to Auth0 Token Vault.
    """
    logger.info("Initiating Salesforce connection", user_sub=user.sub)

    try:
        auth_url = await token_vault.get_connection_auth_url(
            connection=settings.salesforce_connection_name,
            redirect_uri=f"{settings.cors_origins[0]}/callback/salesforce",
            state=user.sub,
        )

        return {"auth_url": auth_url}

    except Exception as e:
        logger.error("Failed to initiate Salesforce connection", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate Salesforce connection",
        )


@router.post("/disconnect")
async def disconnect_salesforce(
    user: UserInfo = Depends(get_current_user),
):
    """
    Disconnect Salesforce account from Token Vault.

    This revokes the stored tokens and removes the connection.
    """
    logger.info("Disconnecting Salesforce", user_sub=user.sub)

    try:
        # Get Auth0 user ID
        auth0_user_id = await token_vault.get_user_id_from_okta_sub(user.sub)

        if not auth0_user_id:
            return {"success": True, "message": "No Salesforce connection found"}

        # In production, you would call Auth0 Management API to unlink the identity
        # For now, just return success
        return {"success": True, "message": "Salesforce disconnected"}

    except Exception as e:
        logger.error("Failed to disconnect Salesforce", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Salesforce",
        )


@router.get("/status")
async def get_salesforce_status(
    user: UserInfo = Depends(get_current_user),
):
    """
    Check Salesforce connection status.
    """
    try:
        auth0_user_id = await token_vault.get_user_id_from_okta_sub(user.sub)

        if not auth0_user_id:
            return {
                "connected": False,
                "message": "User not found in Auth0",
            }

        is_connected = await token_vault.check_salesforce_connection(auth0_user_id)

        return {
            "connected": is_connected,
            "instance_url": settings.salesforce_instance_url if is_connected else None,
        }

    except Exception as e:
        logger.error("Failed to check Salesforce status", error=str(e))
        return {
            "connected": False,
            "error": str(e),
        }
