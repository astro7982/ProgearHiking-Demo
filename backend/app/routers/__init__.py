"""API Routers for ProGear Hiking AI Agent."""

from app.routers.user import router as user_router
from app.routers.chat import router as chat_router
from app.routers.salesforce import router as salesforce_router
from app.routers.inventory import router as inventory_router

__all__ = [
    "user_router",
    "chat_router",
    "salesforce_router",
    "inventory_router",
]
