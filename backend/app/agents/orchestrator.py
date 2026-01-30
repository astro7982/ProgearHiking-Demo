"""
Agent Orchestrator

Orchestrates AI agent interactions using Azure AI Foundry.
Routes queries to appropriate MCP tools based on intent analysis.
"""

import json
from typing import Optional, List, Dict, Any
import httpx
import structlog
from enum import Enum

from app.core.config import settings
from app.models.schemas import (
    UserInfo,
    ChatMessage,
    MessageRole,
    AgentType,
    ToolCall,
)
from app.tools.salesforce_tools import SalesforceTools
from app.tools.inventory_tools import inventory_tools

logger = structlog.get_logger()


class ToolCategory(str, Enum):
    """Categories of available tools"""
    SALES = "sales"
    CUSTOMER = "customer"
    INVENTORY = "inventory"
    GENERAL = "general"


# Tool definitions for Azure AI Foundry
AVAILABLE_TOOLS = [
    # Salesforce - Sales Tools
    {
        "type": "function",
        "function": {
            "name": "get_opportunities",
            "description": "Get sales opportunities from Salesforce CRM. Shows pipeline, deals, revenue forecasts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max number of opportunities to return", "default": 10},
                    "stage": {"type": "string", "description": "Filter by stage (Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_accounts",
            "description": "Search Salesforce accounts/companies by name or criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Search term for account name"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_leads",
            "description": "Get sales leads from Salesforce",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Lead status filter"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_opportunity",
            "description": "Create a new sales opportunity in Salesforce",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Opportunity name"},
                    "amount": {"type": "number", "description": "Deal value"},
                    "stage": {"type": "string", "description": "Sales stage"},
                    "close_date": {"type": "string", "description": "Expected close date (YYYY-MM-DD)"},
                    "account_id": {"type": "string", "description": "Associated account ID"},
                },
                "required": ["name", "stage", "close_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_analytics",
            "description": "Get sales analytics and performance metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "Time period (THIS_MONTH, LAST_MONTH, THIS_QUARTER, THIS_YEAR)"},
                },
                "required": [],
            },
        },
    },
    # Salesforce - Customer Tools
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search customer contacts in Salesforce",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Name or email to search"},
                    "account_id": {"type": "string", "description": "Filter by account"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_history",
            "description": "Get customer interaction and purchase history",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Account ID"},
                    "include_opportunities": {"type": "boolean", "default": True},
                    "include_activities": {"type": "boolean", "default": True},
                },
                "required": ["account_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_activity",
            "description": "Log a customer activity (call, email, meeting) in Salesforce",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Activity subject"},
                    "activity_type": {"type": "string", "description": "Type: Call, Email, Meeting, Task"},
                    "description": {"type": "string", "description": "Activity details"},
                    "contact_id": {"type": "string", "description": "Related contact ID"},
                    "account_id": {"type": "string", "description": "Related account ID"},
                },
                "required": ["subject", "activity_type"],
            },
        },
    },
    # Inventory Tools
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check current inventory levels for products. Can filter by category or search for specific items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Product category (footwear, apparel, equipment, accessories)"},
                    "sku": {"type": "string", "description": "Specific product SKU"},
                    "search": {"type": "string", "description": "Search term for product name"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_inventory",
            "description": "Update inventory quantity for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU"},
                    "quantity_change": {"type": "integer", "description": "Amount to add (positive) or remove (negative)"},
                    "reason": {"type": "string", "description": "Reason for the change"},
                },
                "required": ["sku", "quantity_change", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_alerts",
            "description": "Get products that are low in stock or need reordering",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "integer", "description": "Stock level threshold", "default": 15},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reorder",
            "description": "Create a reorder request for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU to reorder"},
                    "quantity": {"type": "integer", "description": "Quantity to order"},
                },
                "required": ["sku", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_analytics",
            "description": "Get inventory analytics including stock value, turnover, and trends",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_movements",
            "description": "Get history of stock movements for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["sku"],
            },
        },
    },
]


class AgentOrchestrator:
    """
    Orchestrates AI agent interactions with Azure AI Foundry.

    Handles:
    - Intent analysis and routing
    - Tool execution with proper authorization
    - Response synthesis
    """

    def __init__(
        self,
        user: UserInfo,
        salesforce_tools: Optional[SalesforceTools] = None,
        user_scopes: Optional[List[str]] = None,
    ):
        self.user = user
        self.salesforce_tools = salesforce_tools
        self.user_scopes = user_scopes or []
        self.conversation_history: List[Dict[str, Any]] = []

    def _get_system_prompt(self) -> str:
        """Generate system prompt for the AI agent"""
        scope_info = ", ".join(self.user_scopes) if self.user_scopes else "demo access"

        return f"""You are ProGear AI, an intelligent assistant for ProGear Hiking outdoor gear retail company.

You help employees manage:
- **Sales**: Opportunities, quotes, pipeline, and revenue tracking (via Salesforce)
- **Customers**: Accounts, contacts, interaction history (via Salesforce)
- **Inventory**: Stock levels, products, reorders, and alerts (internal system)

Current User: {self.user.name or self.user.email}
Available Access: {scope_info}

Guidelines:
1. Be helpful and proactive in finding information
2. When using tools, explain what you're doing
3. Format responses clearly with relevant data
4. If access is denied to a resource, explain politely and suggest alternatives
5. For inventory questions, use the check_inventory or get_low_stock_alerts tools
6. For sales/customer questions, use the Salesforce tools
7. Always provide actionable insights when presenting data

Remember: This is a demo showcasing Okta AI Agent governance with XAA token exchange and Auth0 Token Vault integration."""

    async def _call_azure_foundry(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Call Azure AI Foundry API"""
        if not settings.azure_foundry_endpoint or not settings.azure_foundry_api_key:
            logger.warning("Azure Foundry not configured, using mock response")
            return self._mock_response(messages)

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Content-Type": "application/json",
                "api-key": settings.azure_foundry_api_key,
            }

            payload = {
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            }

            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            # Azure AI Foundry uses /openai/deployments/{deployment}/chat/completions format
            deployment = settings.azure_foundry_deployment or "gpt-4o"
            endpoint = settings.azure_foundry_endpoint.rstrip("/")

            # Try the project-based endpoint format first
            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-08-01-preview"

            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("Azure Foundry API error", status=e.response.status_code, detail=str(e))
                # Fall back to mock response on error
                return self._mock_response(messages)
            except Exception as e:
                logger.error("Azure Foundry connection error", error=str(e))
                return self._mock_response(messages)

    def _mock_response(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate mock response when Azure Foundry is not configured"""
        last_message = messages[-1]["content"] if messages else ""
        last_lower = last_message.lower()

        # Determine appropriate mock response based on query
        if any(word in last_lower for word in ["inventory", "stock", "product"]):
            response_text = """I can help you check our inventory! Here's what I found:

**Current Stock Summary:**
- Trail Runner Pro (TRP-001): 45 units ✓ In Stock
- Summit Hiking Boot (SHB-002): 12 units ⚠️ Low Stock
- Alpine Backpack 45L (ABP-003): 28 units ✓ In Stock
- Weather Shield Jacket (WSJ-004): 0 units ❌ Out of Stock

⚠️ **Alert**: We have 3 items that need attention - consider reordering the Weather Shield Jacket and Summit Hiking Boot."""

        elif any(word in last_lower for word in ["sales", "opportunity", "deal", "pipeline"]):
            response_text = """Here's your sales pipeline overview:

**Active Opportunities:**
| Deal | Amount | Stage | Close Date |
|------|--------|-------|------------|
| REI Partnership | $125,000 | Proposal | Mar 15 |
| Outdoor World Bulk | $89,500 | Negotiation | Feb 28 |
| Adventure Co. Renewal | $45,000 | Closed Won | Feb 10 |

**Pipeline Summary:**
- Total Pipeline Value: $259,500
- Weighted Value: $178,250
- Win Rate This Quarter: 68%"""

        elif any(word in last_lower for word in ["customer", "account", "contact"]):
            response_text = """Here are your recent customer accounts:

**Top Accounts:**
1. **REI Cooperative** - $450K annual revenue
   - Primary Contact: Sarah Johnson (sarah@rei.com)
   - Last Activity: Meeting on Feb 5th

2. **Outdoor World** - $280K annual revenue
   - Primary Contact: Mike Chen (mike@outdoorworld.com)
   - Last Activity: Quote sent Feb 8th

3. **Adventure Outfitters** - $175K annual revenue
   - Primary Contact: Lisa Park
   - Last Activity: Contract signed Feb 1st"""

        else:
            response_text = f"""Hello {self.user.name or 'there'}! I'm ProGear AI, your assistant for managing sales, customers, and inventory.

I can help you with:
- 📊 **Sales**: Check opportunities, pipeline, create quotes
- 👥 **Customers**: Look up accounts, contacts, interaction history
- 📦 **Inventory**: Check stock levels, manage products, handle reorders

What would you like to know about today?"""

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop",
            }],
        }

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results"""
        logger.info("Executing tool", tool=tool_name, arguments=arguments)

        try:
            # Inventory tools
            if tool_name == "check_inventory":
                if arguments.get("sku"):
                    product = inventory_tools.get_product(arguments["sku"])
                    return {"product": product.__dict__ if product else None}
                else:
                    products = inventory_tools.list_products(
                        category=arguments.get("category"),
                    )
                    if arguments.get("search"):
                        search = arguments["search"].lower()
                        products = [p for p in products if search in p.name.lower()]
                    return {"products": [p.__dict__ for p in products]}

            elif tool_name == "update_inventory":
                result = inventory_tools.update_stock_sync(
                    sku=arguments["sku"],
                    quantity_change=arguments["quantity_change"],
                    reason=arguments["reason"],
                )
                return result

            elif tool_name == "get_low_stock_alerts":
                result = inventory_tools.check_low_stock(
                    threshold=arguments.get("threshold", 15)
                )
                return result

            elif tool_name == "create_reorder":
                result = inventory_tools.create_reorder(
                    sku=arguments["sku"],
                    quantity=arguments["quantity"],
                )
                return result

            elif tool_name == "get_inventory_analytics":
                return inventory_tools.get_inventory_summary()

            elif tool_name == "get_stock_movements":
                movements = inventory_tools.get_stock_movements(arguments["sku"])
                return {"movements": movements}

            # Salesforce tools
            elif tool_name in ["get_opportunities", "search_accounts", "get_leads",
                               "create_opportunity", "get_sales_analytics",
                               "search_contacts", "get_customer_history", "create_activity"]:
                if self.salesforce_tools:
                    # Map tool name to Salesforce method
                    method_map = {
                        "get_opportunities": "get_opportunities",
                        "search_accounts": "search_accounts",
                        "get_leads": "get_leads",
                        "create_opportunity": "create_opportunity",
                        "get_sales_analytics": "get_sales_analytics",
                        "search_contacts": "search_contacts",
                        "get_customer_history": "get_account_history",
                        "create_activity": "log_activity",
                    }
                    method = getattr(self.salesforce_tools, method_map[tool_name], None)
                    if method:
                        result = await method(**arguments)
                        return result
                    return {"error": f"Method {tool_name} not found"}
                else:
                    return {
                        "error": "Salesforce not connected",
                        "message": "Please connect your Salesforce account to access sales and customer data",
                    }

            return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            return {"error": str(e)}

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> ChatMessage:
        """Process a user message and return AI response"""
        logger.info(
            "Processing message",
            user=self.user.email,
            message_preview=message[:100],
        )

        # Build messages for AI
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
        ]

        # Add conversation history
        for hist in self.conversation_history[-10:]:  # Keep last 10 messages
            messages.append(hist)

        # Add current message
        messages.append({"role": "user", "content": message})

        # Call Azure Foundry
        tool_calls = []
        try:
            response = await self._call_azure_foundry(messages, AVAILABLE_TOOLS)
            choice = response["choices"][0]
            assistant_message = choice["message"]

            # Handle tool calls if present
            if "tool_calls" in assistant_message:
                for tool_call in assistant_message["tool_calls"]:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    arguments = json.loads(func.get("arguments", "{}"))

                    # Execute tool
                    result = await self._execute_tool(tool_name, arguments)

                    # Determine agent type based on tool
                    agent_type = AgentType.INVENTORY
                    if tool_name in ["get_opportunities", "create_opportunity",
                                     "get_leads", "get_sales_analytics", "search_accounts"]:
                        agent_type = AgentType.SALES
                    elif tool_name in ["search_contacts", "get_customer_history", "create_activity"]:
                        agent_type = AgentType.CUSTOMER

                    tool_calls.append(ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result,
                        agent=agent_type,
                    ))

                # If we had tool calls, get a follow-up response
                messages.append(assistant_message)
                for tc in tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tc.result),
                    })

                final_response = await self._call_azure_foundry(messages)
                content = final_response["choices"][0]["message"]["content"]
            else:
                content = assistant_message.get("content", "")

        except Exception as e:
            logger.error("AI processing failed", error=str(e))
            content = f"I encountered an issue processing your request. Please try again. (Error: {str(e)})"

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": content})

        # Determine primary agent used
        agents_used = list(set(tc.agent for tc in tool_calls)) if tool_calls else [AgentType.GENERAL]

        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            agent=agents_used[0] if len(agents_used) == 1 else AgentType.GENERAL,
            tool_calls=tool_calls if tool_calls else None,
        )
