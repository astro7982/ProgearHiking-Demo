"""
Chat Router

Main chat endpoint that orchestrates:
- Message analysis and routing
- Tool selection and execution
- Response generation via Azure AI Foundry
"""

import uuid
import time
import json
from typing import Optional, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import structlog

from app.auth.okta_auth import get_current_user, get_id_token, okta_auth
from app.auth.token_vault import token_vault
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AgentInfo,
    AgentType,
    ToolCall,
    ToolCallStatus,
    UserInfo,
)
from app.tools.salesforce_tools import SalesforceTools
from app.tools.inventory_tools import InventoryTools, inventory_tools
from app.agents.orchestrator import AgentOrchestrator as AIOrchestrator
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


class AgentOrchestrator:
    """Orchestrates chat requests between different MCP agents"""

    def __init__(
        self,
        user: UserInfo,
        id_token: str,
        salesforce_token: Optional[str] = None,
        inventory_scopes: list[str] = None,
    ):
        self.user = user
        self.id_token = id_token
        self.salesforce_token = salesforce_token
        self.inventory_scopes = inventory_scopes or []

    def analyze_intent(self, message: str) -> tuple[AgentType, list[str]]:
        """
        Analyze message to determine which agent(s) to use.
        Returns (primary_agent, required_tools).
        """
        message_lower = message.lower()

        # Salesforce keywords
        salesforce_keywords = [
            "sales", "lead", "opportunity", "customer", "account",
            "contact", "pipeline", "deal", "prospect", "crm",
            "revenue", "close", "won", "lost", "quote",
        ]

        # Inventory keywords
        inventory_keywords = [
            "inventory", "stock", "product", "warehouse", "quantity",
            "reorder", "alert", "sku", "item", "supply",
            "boot", "tent", "backpack", "jacket", "gear", "equipment",
        ]

        salesforce_score = sum(1 for kw in salesforce_keywords if kw in message_lower)
        inventory_score = sum(1 for kw in inventory_keywords if kw in message_lower)

        if salesforce_score > inventory_score:
            return AgentType.SALESFORCE, self._get_salesforce_tools(message_lower)
        elif inventory_score > 0:
            return AgentType.INVENTORY, self._get_inventory_tools(message_lower)
        else:
            # Default to orchestrator for general queries
            return AgentType.ORCHESTRATOR, []

    def _get_salesforce_tools(self, message: str) -> list[str]:
        """Determine which Salesforce tools to use"""
        tools = []

        if any(w in message for w in ["lead", "leads"]):
            if any(w in message for w in ["create", "add", "new"]):
                tools.append("create_lead")
            elif any(w in message for w in ["update", "change", "status"]):
                tools.append("update_lead_status")
            else:
                tools.append("get_leads")

        if any(w in message for w in ["opportunity", "opportunities", "deal", "pipeline"]):
            if any(w in message for w in ["create", "add", "new"]):
                tools.append("create_opportunity")
            elif any(w in message for w in ["update", "stage"]):
                tools.append("update_opportunity_stage")
            elif any(w in message for w in ["summary", "overview"]):
                tools.append("get_pipeline_summary")
            else:
                tools.append("get_opportunities")

        if any(w in message for w in ["account", "accounts", "company", "companies"]):
            if any(w in message for w in ["detail", "info", "about"]):
                tools.append("get_account_details")
            else:
                tools.append("get_accounts")

        if any(w in message for w in ["contact", "contacts"]):
            if any(w in message for w in ["create", "add", "new"]):
                tools.append("create_contact")
            else:
                tools.append("get_contacts")

        if any(w in message for w in ["activity", "activities", "recent"]):
            tools.append("get_recent_activities")

        return tools or ["get_leads", "get_opportunities"]

    def _get_inventory_tools(self, message: str) -> list[str]:
        """Determine which Inventory tools to use"""
        tools = []

        if any(w in message for w in ["check", "level", "status", "how many", "quantity"]):
            tools.append("check_stock")

        if any(w in message for w in ["update", "add", "increase", "decrease", "adjust"]):
            tools.append("update_stock")

        if any(w in message for w in ["alert", "alerts", "warning"]):
            if any(w in message for w in ["create", "set", "new"]):
                tools.append("create_alert")
            elif any(w in message for w in ["dismiss", "clear", "remove"]):
                tools.append("dismiss_alert")
            else:
                tools.append("get_alerts")

        if any(w in message for w in ["detail", "info", "about"]) and any(
            w in message for w in ["product", "item"]
        ):
            tools.append("get_product_details")

        if any(w in message for w in ["search", "find", "look"]):
            tools.append("search_products")

        if any(w in message for w in ["summary", "overview", "total", "report"]):
            if any(w in message for w in ["low", "reorder"]):
                tools.append("get_low_stock_report")
            elif any(w in message for w in ["category", "breakdown"]):
                tools.append("get_category_breakdown")
            else:
                tools.append("get_stock_summary")

        return tools or ["check_stock"]

    async def execute_salesforce_tools(
        self,
        tools: list[str],
        message: str,
    ) -> tuple[list[ToolCall], str]:
        """Execute Salesforce tools and generate response"""
        if not self.salesforce_token:
            return [], "I don't have access to Salesforce. Please connect your Salesforce account first."

        sf_tools = SalesforceTools(
            access_token=self.salesforce_token,
            instance_url=settings.salesforce_instance_url,
        )

        tool_calls = []
        results = []

        for tool_name in tools:
            if tool_name == "get_leads":
                tool_call = await sf_tools.get_leads(limit=10)
            elif tool_name == "get_opportunities":
                tool_call = await sf_tools.get_opportunities(limit=10)
            elif tool_name == "get_accounts":
                tool_call = await sf_tools.get_accounts(limit=10)
            elif tool_name == "get_contacts":
                tool_call = await sf_tools.get_contacts(limit=10)
            elif tool_name == "get_pipeline_summary":
                tool_call = await sf_tools.get_pipeline_summary()
            elif tool_name == "get_recent_activities":
                tool_call = await sf_tools.get_recent_activities()
            else:
                continue

            tool_calls.append(tool_call)

            if tool_call.status == ToolCallStatus.COMPLETED and tool_call.result:
                results.append(tool_call.result)

        # Generate response from results
        response = self._format_salesforce_response(tools, results)

        return tool_calls, response

    async def execute_inventory_tools(
        self,
        tools: list[str],
        message: str,
    ) -> tuple[list[ToolCall], str]:
        """Execute Inventory tools and generate response"""
        inv_tools = InventoryTools(user_scopes=self.inventory_scopes)

        tool_calls = []
        results = []

        for tool_name in tools:
            if tool_name == "check_stock":
                # Try to extract SKU or category from message
                tool_call = await inv_tools.check_stock()
            elif tool_name == "get_stock_summary":
                tool_call = await inv_tools.get_stock_summary()
            elif tool_name == "get_low_stock_report":
                tool_call = await inv_tools.get_low_stock_report()
            elif tool_name == "get_category_breakdown":
                tool_call = await inv_tools.get_category_breakdown()
            elif tool_name == "get_alerts":
                tool_call = await inv_tools.get_alerts()
            elif tool_name == "search_products":
                # Extract search query
                query = message.split("search")[-1].strip() if "search" in message else message
                tool_call = await inv_tools.search_products(query=query[:50])
            elif tool_name == "update_stock":
                # For demo, we'll need more structured input
                tool_call = await inv_tools.get_stock_summary()
            else:
                continue

            tool_calls.append(tool_call)

            if tool_call.status == ToolCallStatus.COMPLETED and tool_call.result:
                results.append(tool_call.result)

        # Generate response from results
        response = self._format_inventory_response(tools, results)

        return tool_calls, response

    def _format_salesforce_response(
        self,
        tools: list[str],
        results: list[dict],
    ) -> str:
        """Format Salesforce results into a readable response"""
        if not results:
            return "I wasn't able to retrieve any Salesforce data at this time."

        parts = []

        for i, result in enumerate(results):
            tool = tools[i] if i < len(tools) else "unknown"

            if "leads" in result:
                leads = result["leads"]
                if leads:
                    parts.append(f"**Found {len(leads)} leads:**\n")
                    for lead in leads[:5]:
                        parts.append(f"- {lead['name']} ({lead['company']}) - {lead['status']}")
                else:
                    parts.append("No leads found matching your criteria.")

            elif "opportunities" in result:
                opps = result["opportunities"]
                if opps:
                    parts.append(f"**Found {len(opps)} opportunities:**\n")
                    for opp in opps[:5]:
                        amount = f"${opp['amount']:,.0f}" if opp.get("amount") else "TBD"
                        parts.append(f"- {opp['name']} - {amount} ({opp['stage']})")
                    if result.get("total_pipeline_value"):
                        parts.append(f"\n**Total pipeline value:** ${result['total_pipeline_value']:,.0f}")
                else:
                    parts.append("No opportunities found matching your criteria.")

            elif "accounts" in result:
                accounts = result["accounts"]
                if accounts:
                    parts.append(f"**Found {len(accounts)} accounts:**\n")
                    for acc in accounts[:5]:
                        industry = acc.get("industry") or "N/A"
                        parts.append(f"- {acc['name']} ({industry})")
                else:
                    parts.append("No accounts found.")

            elif "contacts" in result:
                contacts = result["contacts"]
                if contacts:
                    parts.append(f"**Found {len(contacts)} contacts:**\n")
                    for contact in contacts[:5]:
                        email = contact.get("email") or "no email"
                        parts.append(f"- {contact['name']} - {email}")
                else:
                    parts.append("No contacts found.")

            elif "stages" in result:
                parts.append("**Pipeline Summary:**\n")
                for stage in result["stages"]:
                    parts.append(
                        f"- {stage['stage']}: {stage['count']} opportunities (${stage['total_amount']:,.0f})"
                    )
                parts.append(f"\n**Total:** ${result.get('total_pipeline_value', 0):,.0f}")

        return "\n".join(parts) if parts else "Salesforce query completed."

    def _format_inventory_response(
        self,
        tools: list[str],
        results: list[dict],
    ) -> str:
        """Format Inventory results into a readable response"""
        if not results:
            return "I wasn't able to retrieve inventory data at this time."

        parts = []

        for i, result in enumerate(results):
            if "error" in result:
                parts.append(f"Error: {result['error']}")
                continue

            if "products" in result:
                products = result["products"]
                if products:
                    parts.append(f"**Found {len(products)} products:**\n")
                    parts.append("| SKU | Name | Qty | Status |")
                    parts.append("|-----|------|-----|--------|")
                    for prod in products[:10]:
                        status_emoji = "🟢" if prod["status"] == "in_stock" else "🟡" if prod["status"] == "low_stock" else "🔴"
                        parts.append(
                            f"| {prod['sku']} | {prod['name']} | {prod['quantity']} | {status_emoji} {prod['status']} |"
                        )
                else:
                    parts.append("No products found matching your criteria.")

            elif "total_products" in result:
                # Stock summary
                parts.append("**Inventory Summary:**\n")
                parts.append(f"- **Total Products:** {result['total_products']}")
                parts.append(f"- **Total Units:** {result['total_units']}")
                parts.append(f"- **Total Value:** ${result['total_inventory_value']:,.2f}")
                parts.append(f"- **In Stock:** {result.get('in_stock_count', 0)}")
                parts.append(f"- **Low Stock:** {result['low_stock_count']} ⚠️")
                parts.append(f"- **Out of Stock:** {result['out_of_stock_count']} 🔴")

                if result.get("active_alerts", 0) > 0:
                    parts.append(f"\n**Active Alerts:** {result['active_alerts']}")

            elif "items" in result:
                # Low stock report
                items = result["items"]
                if items:
                    parts.append(f"**⚠️ {len(items)} items need attention:**\n")
                    for item in items[:10]:
                        parts.append(
                            f"- **{item['name']}** (SKU: {item['sku']}): "
                            f"{item['current_quantity']}/{item['reorder_point']} - "
                            f"Need to order {item['shortage']} units"
                        )
                else:
                    parts.append("All products are well stocked! 🎉")

            elif "alerts" in result:
                alerts = result["alerts"]
                if alerts:
                    parts.append(f"**{len(alerts)} Active Alerts:**\n")
                    for alert in alerts:
                        emoji = "🔴" if alert["alert_type"] == "out_of_stock" else "🟡"
                        parts.append(
                            f"- {emoji} **{alert['product_name']}**: {alert['alert_type']} "
                            f"(Current: {alert['current_quantity']}, Threshold: {alert['threshold']})"
                        )
                else:
                    parts.append("No active inventory alerts.")

            elif "categories" in result:
                parts.append("**Inventory by Category:**\n")
                for cat, data in result["categories"].items():
                    parts.append(
                        f"- **{cat.title()}**: {data['product_count']} products, "
                        f"{data['total_units']} units, ${data['total_value']:,.2f} value"
                    )

        return "\n".join(parts) if parts else "Inventory query completed."


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: UserInfo = Depends(get_current_user),
    id_token: str = Depends(get_id_token),
):
    """
    Main chat endpoint.

    Analyzes the message, routes to appropriate agent(s),
    executes tools, and returns response.
    """
    logger.info(
        "Chat request received",
        user_sub=user.sub,
        message_length=len(request.message),
    )

    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Get user's service connections
    salesforce_token = None
    inventory_scopes = ["inventory:read", "inventory:write", "inventory:alert"]

    # Try to get Salesforce token from Token Vault
    try:
        auth0_user_id = await token_vault.get_user_id_from_okta_sub(user.sub)
        if auth0_user_id:
            sf_result = await token_vault.get_salesforce_token(auth0_user_id)
            if sf_result.get("success"):
                salesforce_token = sf_result.get("access_token")
    except Exception as e:
        logger.warning("Failed to get Salesforce token", error=str(e))

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        user=user,
        id_token=id_token,
        salesforce_token=salesforce_token,
        inventory_scopes=inventory_scopes,
    )

    # Analyze intent and determine agent
    agent_type, tools = orchestrator.analyze_intent(request.message)

    # Execute appropriate tools
    tool_calls = []
    response_text = ""

    if agent_type == AgentType.SALESFORCE:
        tool_calls, response_text = await orchestrator.execute_salesforce_tools(
            tools, request.message
        )
        agent_name = "Salesforce Agent"
        scopes = ["sales:read", "customer:read"] if salesforce_token else []

    elif agent_type == AgentType.INVENTORY:
        tool_calls, response_text = await orchestrator.execute_inventory_tools(
            tools, request.message
        )
        agent_name = "Inventory Agent"
        scopes = inventory_scopes

    else:
        # Default orchestrator response
        agent_name = "ProGear Assistant"
        agent_type = AgentType.ORCHESTRATOR
        scopes = []
        response_text = """I can help you with:

**Salesforce** (Sales & Customers)
- View and manage leads
- Track opportunities and pipeline
- Search customer accounts
- View contact information

**Inventory**
- Check stock levels
- Update inventory quantities
- Set low-stock alerts
- View product catalog

What would you like to know?"""

    duration = int((time.time() - start_time) * 1000)
    logger.info(
        "Chat response generated",
        agent=agent_type.value,
        tools_used=len(tool_calls),
        duration_ms=duration,
    )

    return ChatResponse(
        id=str(uuid.uuid4()),
        message=response_text,
        agent=AgentInfo(
            name=agent_name,
            type=agent_type,
            scopes=scopes,
        ),
        tool_calls=tool_calls,
        conversation_id=conversation_id,
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: UserInfo = Depends(get_current_user),
    id_token: str = Depends(get_id_token),
):
    """
    Streaming chat endpoint for real-time responses.
    Returns Server-Sent Events.
    """

    async def generate() -> AsyncGenerator[str, None]:
        # For now, just call the regular chat endpoint and stream the result
        response = await chat(request, user, id_token)

        # Stream tool calls
        for tool_call in response.tool_calls:
            yield f"data: {json.dumps({'type': 'tool_call', 'tool_call': tool_call.model_dump()})}\n\n"

        # Stream the response in chunks (simulated)
        words = response.message.split(" ")
        chunk = ""
        for i, word in enumerate(words):
            chunk += word + " "
            if i % 5 == 4 or i == len(words) - 1:
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                chunk = ""

        # Send complete signal
        yield f"data: {json.dumps({'type': 'complete', 'response': response.model_dump()})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/ai", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    user: UserInfo = Depends(get_current_user),
    id_token: str = Depends(get_id_token),
):
    """
    AI-powered chat endpoint using Azure AI Foundry.

    This endpoint uses the full AI orchestrator with:
    - Natural language understanding
    - Automatic tool selection
    - Contextual response generation
    """
    logger.info(
        "AI chat request received",
        user_sub=user.sub,
        message_length=len(request.message),
    )

    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Try to get Salesforce token from Token Vault
    salesforce_tools = None
    try:
        auth0_user_id = await token_vault.get_user_id_from_okta_sub(user.sub)
        if auth0_user_id:
            sf_result = await token_vault.get_salesforce_token(auth0_user_id)
            if sf_result.get("success"):
                salesforce_tools = SalesforceTools(
                    access_token=sf_result.get("access_token"),
                    instance_url=settings.salesforce_instance_url,
                )
    except Exception as e:
        logger.warning("Failed to get Salesforce token", error=str(e))

    # Create AI orchestrator
    ai_orchestrator = AIOrchestrator(
        user=user,
        salesforce_tools=salesforce_tools,
        user_scopes=["inventory:read", "inventory:write", "inventory:alert"],
    )

    # Process message with AI
    ai_message = await ai_orchestrator.process_message(
        message=request.message,
        conversation_id=conversation_id,
    )

    duration = int((time.time() - start_time) * 1000)
    logger.info(
        "AI chat response generated",
        agent=ai_message.agent.value if ai_message.agent else "general",
        tools_used=len(ai_message.tool_calls) if ai_message.tool_calls else 0,
        duration_ms=duration,
    )

    # Map agent type to agent name
    agent_names = {
        AgentType.SALES: "Sales Agent",
        AgentType.CUSTOMER: "Customer Agent",
        AgentType.INVENTORY: "Inventory Agent",
        AgentType.SALESFORCE: "Salesforce Agent",
        AgentType.ORCHESTRATOR: "ProGear AI",
        AgentType.GENERAL: "ProGear Assistant",
    }

    return ChatResponse(
        id=str(uuid.uuid4()),
        message=ai_message.content,
        agent=AgentInfo(
            name=agent_names.get(ai_message.agent, "ProGear AI"),
            type=ai_message.agent or AgentType.GENERAL,
            scopes=["inventory:read", "inventory:write"] if ai_message.agent == AgentType.INVENTORY else [],
        ),
        tool_calls=[
            ToolCall(
                tool_name=tc.tool_name,
                arguments=tc.arguments,
                result=tc.result,
                status=ToolCallStatus.COMPLETED if tc.result else ToolCallStatus.FAILED,
            )
            for tc in (ai_message.tool_calls or [])
        ],
        conversation_id=conversation_id,
    )
