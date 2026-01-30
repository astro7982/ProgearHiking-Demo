"""
Salesforce MCP Tools

Comprehensive tools for interacting with Salesforce CRM:
- Accounts & Contacts
- Leads & Opportunities
- Activities & Tasks
- Reports & Analytics
"""

import time
from typing import Optional, Any
from datetime import datetime, timedelta
import structlog

from app.models.schemas import (
    ToolCall,
    ToolCallStatus,
    SalesforceAccount,
    SalesforceContact,
    SalesforceLead,
    SalesforceOpportunity,
)

logger = structlog.get_logger()


class SalesforceTools:
    """MCP Tools for Salesforce CRM operations"""

    def __init__(self, access_token: str, instance_url: str):
        self.access_token = access_token
        self.instance_url = instance_url
        self._sf = None

    @property
    def sf(self):
        """Lazy-load Salesforce client"""
        if self._sf is None:
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                instance_url=self.instance_url,
                session_id=self.access_token,
            )
        return self._sf

    async def _execute_tool(
        self,
        tool_name: str,
        func,
        **kwargs,
    ) -> ToolCall:
        """Execute a tool and return standardized result"""
        tool_id = f"sf-{tool_name}-{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            result = await func(**kwargs) if callable(func) else func
            duration = int((time.time() - start_time) * 1000)

            return ToolCall(
                id=tool_id,
                name=f"salesforce.{tool_name}",
                status=ToolCallStatus.COMPLETED,
                arguments=kwargs,
                result=result,
                duration=duration,
            )
        except Exception as e:
            logger.error(f"Salesforce tool error: {tool_name}", error=str(e))
            return ToolCall(
                id=tool_id,
                name=f"salesforce.{tool_name}",
                status=ToolCallStatus.ERROR,
                arguments=kwargs,
                error=str(e),
                duration=int((time.time() - start_time) * 1000),
            )

    # === ACCOUNT TOOLS ===

    async def get_accounts(
        self,
        limit: int = 20,
        search: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> ToolCall:
        """Get Salesforce accounts with optional filtering"""

        async def _execute():
            conditions = []
            if search:
                conditions.append(f"Name LIKE '%{search}%'")
            if industry:
                conditions.append(f"Industry = '{industry}'")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT Id, Name, Industry, Website, Phone, BillingCity, BillingState
                FROM Account
                {where_clause}
                ORDER BY Name
                LIMIT {limit}
            """

            result = self.sf.query(query)
            accounts = [
                {
                    "id": r["Id"],
                    "name": r["Name"],
                    "industry": r.get("Industry"),
                    "website": r.get("Website"),
                    "phone": r.get("Phone"),
                    "billing_city": r.get("BillingCity"),
                    "billing_state": r.get("BillingState"),
                }
                for r in result.get("records", [])
            ]

            return {
                "accounts": accounts,
                "total_count": result.get("totalSize", 0),
            }

        return await self._execute_tool(
            "get_accounts",
            _execute,
            limit=limit,
            search=search,
            industry=industry,
        )

    async def get_account_details(self, account_id: str) -> ToolCall:
        """Get detailed information about a specific account"""

        async def _execute():
            account = self.sf.Account.get(account_id)
            return {
                "id": account["Id"],
                "name": account["Name"],
                "industry": account.get("Industry"),
                "website": account.get("Website"),
                "phone": account.get("Phone"),
                "description": account.get("Description"),
                "billing_address": {
                    "street": account.get("BillingStreet"),
                    "city": account.get("BillingCity"),
                    "state": account.get("BillingState"),
                    "postal_code": account.get("BillingPostalCode"),
                    "country": account.get("BillingCountry"),
                },
                "annual_revenue": account.get("AnnualRevenue"),
                "number_of_employees": account.get("NumberOfEmployees"),
                "owner_id": account.get("OwnerId"),
                "created_date": account.get("CreatedDate"),
            }

        return await self._execute_tool("get_account_details", _execute, account_id=account_id)

    # === CONTACT TOOLS ===

    async def get_contacts(
        self,
        account_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> ToolCall:
        """Get contacts with optional filtering by account or search"""

        async def _execute():
            conditions = []
            if account_id:
                conditions.append(f"AccountId = '{account_id}'")
            if search:
                conditions.append(f"(Name LIKE '%{search}%' OR Email LIKE '%{search}%')")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT Id, Name, Email, Phone, Title, AccountId, Account.Name
                FROM Contact
                {where_clause}
                ORDER BY Name
                LIMIT {limit}
            """

            result = self.sf.query(query)
            contacts = [
                {
                    "id": r["Id"],
                    "name": r["Name"],
                    "email": r.get("Email"),
                    "phone": r.get("Phone"),
                    "title": r.get("Title"),
                    "account_id": r.get("AccountId"),
                    "account_name": r.get("Account", {}).get("Name") if r.get("Account") else None,
                }
                for r in result.get("records", [])
            ]

            return {
                "contacts": contacts,
                "total_count": result.get("totalSize", 0),
            }

        return await self._execute_tool(
            "get_contacts",
            _execute,
            account_id=account_id,
            search=search,
            limit=limit,
        )

    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        email: str,
        account_id: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ToolCall:
        """Create a new contact"""

        async def _execute():
            contact_data = {
                "FirstName": first_name,
                "LastName": last_name,
                "Email": email,
            }
            if account_id:
                contact_data["AccountId"] = account_id
            if phone:
                contact_data["Phone"] = phone
            if title:
                contact_data["Title"] = title

            result = self.sf.Contact.create(contact_data)
            return {
                "success": result.get("success", False),
                "id": result.get("id"),
                "name": f"{first_name} {last_name}",
            }

        return await self._execute_tool(
            "create_contact",
            _execute,
            first_name=first_name,
            last_name=last_name,
            email=email,
            account_id=account_id,
        )

    # === LEAD TOOLS ===

    async def get_leads(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
    ) -> ToolCall:
        """Get leads with optional filtering"""

        async def _execute():
            conditions = []
            if status:
                conditions.append(f"Status = '{status}'")
            if source:
                conditions.append(f"LeadSource = '{source}'")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT Id, Name, Company, Email, Phone, Status, LeadSource, CreatedDate
                FROM Lead
                {where_clause}
                ORDER BY CreatedDate DESC
                LIMIT {limit}
            """

            result = self.sf.query(query)
            leads = [
                {
                    "id": r["Id"],
                    "name": r["Name"],
                    "company": r["Company"],
                    "email": r.get("Email"),
                    "phone": r.get("Phone"),
                    "status": r["Status"],
                    "source": r.get("LeadSource"),
                    "created_date": r.get("CreatedDate"),
                }
                for r in result.get("records", [])
            ]

            return {
                "leads": leads,
                "total_count": result.get("totalSize", 0),
            }

        return await self._execute_tool(
            "get_leads",
            _execute,
            status=status,
            source=source,
            limit=limit,
        )

    async def create_lead(
        self,
        first_name: str,
        last_name: str,
        company: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        source: Optional[str] = None,
    ) -> ToolCall:
        """Create a new lead"""

        async def _execute():
            lead_data = {
                "FirstName": first_name,
                "LastName": last_name,
                "Company": company,
                "Status": "New",
            }
            if email:
                lead_data["Email"] = email
            if phone:
                lead_data["Phone"] = phone
            if source:
                lead_data["LeadSource"] = source

            result = self.sf.Lead.create(lead_data)
            return {
                "success": result.get("success", False),
                "id": result.get("id"),
                "name": f"{first_name} {last_name}",
            }

        return await self._execute_tool(
            "create_lead",
            _execute,
            first_name=first_name,
            last_name=last_name,
            company=company,
        )

    async def update_lead_status(self, lead_id: str, new_status: str) -> ToolCall:
        """Update a lead's status"""

        async def _execute():
            self.sf.Lead.update(lead_id, {"Status": new_status})
            return {
                "success": True,
                "lead_id": lead_id,
                "new_status": new_status,
            }

        return await self._execute_tool(
            "update_lead_status",
            _execute,
            lead_id=lead_id,
            new_status=new_status,
        )

    # === OPPORTUNITY TOOLS ===

    async def get_opportunities(
        self,
        stage: Optional[str] = None,
        account_id: Optional[str] = None,
        min_amount: Optional[float] = None,
        limit: int = 20,
    ) -> ToolCall:
        """Get opportunities with optional filtering"""

        async def _execute():
            conditions = []
            if stage:
                conditions.append(f"StageName = '{stage}'")
            if account_id:
                conditions.append(f"AccountId = '{account_id}'")
            if min_amount:
                conditions.append(f"Amount >= {min_amount}")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT Id, Name, Amount, StageName, CloseDate, Probability,
                       AccountId, Account.Name, OwnerId
                FROM Opportunity
                {where_clause}
                ORDER BY CloseDate ASC
                LIMIT {limit}
            """

            result = self.sf.query(query)
            opportunities = [
                {
                    "id": r["Id"],
                    "name": r["Name"],
                    "amount": r.get("Amount"),
                    "stage": r["StageName"],
                    "close_date": r.get("CloseDate"),
                    "probability": r.get("Probability"),
                    "account_id": r.get("AccountId"),
                    "account_name": r.get("Account", {}).get("Name") if r.get("Account") else None,
                }
                for r in result.get("records", [])
            ]

            total_value = sum(o["amount"] or 0 for o in opportunities)

            return {
                "opportunities": opportunities,
                "total_count": result.get("totalSize", 0),
                "total_pipeline_value": total_value,
            }

        return await self._execute_tool(
            "get_opportunities",
            _execute,
            stage=stage,
            account_id=account_id,
            min_amount=min_amount,
            limit=limit,
        )

    async def create_opportunity(
        self,
        name: str,
        stage: str,
        close_date: str,
        amount: Optional[float] = None,
        account_id: Optional[str] = None,
    ) -> ToolCall:
        """Create a new opportunity"""

        async def _execute():
            opp_data = {
                "Name": name,
                "StageName": stage,
                "CloseDate": close_date,
            }
            if amount:
                opp_data["Amount"] = amount
            if account_id:
                opp_data["AccountId"] = account_id

            result = self.sf.Opportunity.create(opp_data)
            return {
                "success": result.get("success", False),
                "id": result.get("id"),
                "name": name,
            }

        return await self._execute_tool(
            "create_opportunity",
            _execute,
            name=name,
            stage=stage,
            close_date=close_date,
            amount=amount,
        )

    async def update_opportunity_stage(
        self,
        opportunity_id: str,
        new_stage: str,
        probability: Optional[int] = None,
    ) -> ToolCall:
        """Update an opportunity's stage"""

        async def _execute():
            update_data = {"StageName": new_stage}
            if probability is not None:
                update_data["Probability"] = probability

            self.sf.Opportunity.update(opportunity_id, update_data)
            return {
                "success": True,
                "opportunity_id": opportunity_id,
                "new_stage": new_stage,
            }

        return await self._execute_tool(
            "update_opportunity_stage",
            _execute,
            opportunity_id=opportunity_id,
            new_stage=new_stage,
        )

    # === ANALYTICS TOOLS ===

    async def get_pipeline_summary(self) -> ToolCall:
        """Get sales pipeline summary by stage"""

        async def _execute():
            query = """
                SELECT StageName, COUNT(Id) opp_count, SUM(Amount) total_amount
                FROM Opportunity
                WHERE IsClosed = false
                GROUP BY StageName
                ORDER BY StageName
            """

            result = self.sf.query(query)
            stages = [
                {
                    "stage": r["StageName"],
                    "count": r["opp_count"],
                    "total_amount": r["total_amount"] or 0,
                }
                for r in result.get("records", [])
            ]

            total_pipeline = sum(s["total_amount"] for s in stages)
            total_opportunities = sum(s["count"] for s in stages)

            return {
                "stages": stages,
                "total_pipeline_value": total_pipeline,
                "total_opportunities": total_opportunities,
            }

        return await self._execute_tool("get_pipeline_summary", _execute)

    async def get_recent_activities(self, days: int = 7, limit: int = 20) -> ToolCall:
        """Get recent activities across leads, contacts, and opportunities"""

        async def _execute():
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

            query = f"""
                SELECT Id, Subject, Status, WhoId, WhatId, ActivityDate, Description
                FROM Task
                WHERE CreatedDate >= {cutoff_date}
                ORDER BY ActivityDate DESC
                LIMIT {limit}
            """

            result = self.sf.query(query)
            activities = [
                {
                    "id": r["Id"],
                    "subject": r["Subject"],
                    "status": r.get("Status"),
                    "activity_date": r.get("ActivityDate"),
                    "description": r.get("Description"),
                }
                for r in result.get("records", [])
            ]

            return {
                "activities": activities,
                "total_count": result.get("totalSize", 0),
                "period_days": days,
            }

        return await self._execute_tool(
            "get_recent_activities",
            _execute,
            days=days,
            limit=limit,
        )
