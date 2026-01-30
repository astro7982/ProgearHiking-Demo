"""
User Router

Endpoints for user information and access management.
"""

from fastapi import APIRouter, Depends
import structlog

from app.auth.okta_auth import get_current_user, get_id_token, okta_auth
from app.auth.token_vault import token_vault
from app.models.schemas import UserInfo, UserAccess, SalesforceAccess, InventoryAccess
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(user: UserInfo = Depends(get_current_user)):
    """Get current user information"""
    return user


@router.get("/access", response_model=UserAccess)
async def get_user_access(
    user: UserInfo = Depends(get_current_user),
    id_token: str = Depends(get_id_token),
):
    """
    Get user's access to different services.

    Checks:
    1. Salesforce connection status via Auth0 Token Vault
    2. Inventory authorization via Okta Custom AS
    """
    logger.info("Checking user access", user_sub=user.sub)

    # Check Salesforce connection
    salesforce_access = SalesforceAccess(connected=False, scopes=[])

    try:
        # Get Auth0 user ID from Okta subject
        auth0_user_id = await token_vault.get_user_id_from_okta_sub(user.sub)

        if auth0_user_id:
            is_connected = await token_vault.check_salesforce_connection(auth0_user_id)
            if is_connected:
                salesforce_access = SalesforceAccess(
                    connected=True,
                    scopes=["sales:read", "sales:write", "customer:read", "customer:lookup"],
                    instance_url=settings.salesforce_instance_url,
                )
    except Exception as e:
        logger.warning("Failed to check Salesforce connection", error=str(e))

    # Check Inventory authorization via Okta Custom AS
    inventory_access = InventoryAccess(authorized=False, scopes=[])

    if settings.inventory_auth_server_id:
        try:
            # Exchange for ID-JAG first
            id_jag = await okta_auth.exchange_for_id_jag(id_token)

            # Exchange ID-JAG for inventory token
            result = await okta_auth.exchange_id_jag_for_token(
                id_jag=id_jag,
                auth_server_id=settings.inventory_auth_server_id,
                scopes=settings.inventory_scopes,
            )

            if result.get("success"):
                inventory_access = InventoryAccess(
                    authorized=True,
                    scopes=result.get("scope", "").split(" "),
                )
        except Exception as e:
            logger.warning("Failed to check inventory authorization", error=str(e))
    else:
        # For demo without custom AS, grant access based on user groups
        if any(g in user.groups for g in ["ProGear-Sales", "ProGear-Warehouse", "Admins"]):
            inventory_access = InventoryAccess(
                authorized=True,
                scopes=["inventory:read", "inventory:write", "inventory:alert"],
            )

    return UserAccess(
        salesforce=salesforce_access,
        inventory=inventory_access,
    )


@router.get("/groups")
async def get_user_groups(user: UserInfo = Depends(get_current_user)):
    """Get user's group memberships"""
    return {
        "groups": user.groups,
        "has_sales_access": "ProGear-Sales" in user.groups,
        "has_warehouse_access": "ProGear-Warehouse" in user.groups,
        "is_admin": "Admins" in user.groups,
    }
