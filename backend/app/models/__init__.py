"""Pydantic models and schemas."""

from app.models.schemas import (
    # Auth
    TokenInfo,
    UserInfo,
    # Agent
    AgentType,
    AgentInfo,
    MessageRole,
    # Chat
    ChatRequest,
    ChatResponse,
    ChatMessage,
    StreamChunk,
    # Tools
    ToolCallStatus,
    ToolCall,
    # User Access
    SalesforceAccess,
    InventoryAccess,
    UserAccess,
    # Salesforce
    SalesforceAccount,
    SalesforceContact,
    SalesforceLead,
    SalesforceOpportunity,
    # Inventory
    ProductCategory,
    StockStatus,
    MovementType,
    AlertSeverity,
    Product,
    InventoryUpdate,
    InventoryAlert,
    StockSummary,
    StockMovement,
)

__all__ = [
    # Auth
    "TokenInfo",
    "UserInfo",
    # Agent
    "AgentType",
    "AgentInfo",
    "MessageRole",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatMessage",
    "StreamChunk",
    # Tools
    "ToolCallStatus",
    "ToolCall",
    # User Access
    "SalesforceAccess",
    "InventoryAccess",
    "UserAccess",
    # Salesforce
    "SalesforceAccount",
    "SalesforceContact",
    "SalesforceLead",
    "SalesforceOpportunity",
    # Inventory
    "ProductCategory",
    "StockStatus",
    "MovementType",
    "AlertSeverity",
    "Product",
    "InventoryUpdate",
    "InventoryAlert",
    "StockSummary",
    "StockMovement",
]
