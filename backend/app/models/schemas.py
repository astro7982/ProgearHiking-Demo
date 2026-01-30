from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# === Auth Models ===

class TokenInfo(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None


class UserInfo(BaseModel):
    sub: str
    email: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    groups: list[str] = []


class AgentType(str, Enum):
    SALESFORCE = "salesforce"
    INVENTORY = "inventory"
    ORCHESTRATOR = "orchestrator"
    SALES = "sales"
    CUSTOMER = "customer"
    GENERAL = "general"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentInfo(BaseModel):
    name: str
    type: AgentType
    scopes: list[str] = []


# === Chat Models ===

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ToolCallStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    name: Optional[str] = None
    tool_name: Optional[str] = None  # Alias for name
    status: ToolCallStatus = ToolCallStatus.PENDING
    arguments: Optional[dict[str, Any]] = None
    result: Optional[Any] = None
    duration: Optional[int] = None  # milliseconds
    error: Optional[str] = None
    agent: Optional[AgentType] = None

    @property
    def effective_name(self) -> str:
        return self.tool_name or self.name or "unknown"


class ChatMessage(BaseModel):
    """A message in a chat conversation"""
    role: MessageRole
    content: str
    agent: Optional[AgentType] = None
    tool_calls: Optional[list[ToolCall]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    id: str
    message: str
    agent: AgentInfo
    tool_calls: list[ToolCall] = []
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    type: str  # "chunk", "tool_call", "complete"
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    response: Optional[ChatResponse] = None


# === User Access Models ===

class SalesforceAccess(BaseModel):
    connected: bool = False
    scopes: list[str] = []
    instance_url: Optional[str] = None


class InventoryAccess(BaseModel):
    authorized: bool = False
    scopes: list[str] = []


class UserAccess(BaseModel):
    salesforce: SalesforceAccess
    inventory: InventoryAccess


# === Salesforce Models ===

class SalesforceAccount(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None


class SalesforceContact(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None


class SalesforceLead(BaseModel):
    id: str
    name: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    source: Optional[str] = None


class SalesforceOpportunity(BaseModel):
    id: str
    name: str
    amount: Optional[float] = None
    stage: str
    close_date: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    probability: Optional[int] = None


# === Inventory Models ===

class ProductCategory(str, Enum):
    FOOTWEAR = "footwear"
    APPAREL = "apparel"
    EQUIPMENT = "equipment"
    ACCESSORIES = "accessories"
    CAMPING = "camping"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class MovementType(str, Enum):
    RECEIVED = "received"
    SOLD = "sold"
    RETURNED = "returned"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    DAMAGED = "damaged"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Product(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str] = None
    category: ProductCategory
    price: float
    cost: Optional[float] = None
    quantity: int
    reorder_point: int = 10
    status: StockStatus
    location: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class InventoryUpdate(BaseModel):
    sku: str
    quantity_change: int  # positive for add, negative for subtract
    reason: Optional[str] = None


class InventoryAlert(BaseModel):
    id: str
    product_id: str
    product_name: str
    sku: str
    alert_type: str  # "low_stock", "out_of_stock", "reorder"
    current_quantity: int
    threshold: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StockSummary(BaseModel):
    total_products: int
    total_value: float
    low_stock_count: int
    out_of_stock_count: int
    categories: dict[str, int]


class StockMovement(BaseModel):
    """Record of a stock quantity change"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    sku: str
    product_name: str
    movement_type: MovementType
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    reason: Optional[str] = None
    performed_by: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
