"""
Inventory MCP Tools

Comprehensive tools for inventory management:
- Stock checking and updates
- Product catalog management
- Alerts and reorder management
- Analytics and reporting
"""

import time
import uuid
from typing import Optional, List
from datetime import datetime
import structlog

from app.models.schemas import (
    ToolCall,
    ToolCallStatus,
    Product,
    ProductCategory,
    StockStatus,
    InventoryAlert,
    StockSummary,
)

logger = structlog.get_logger()


# Demo data - In production, this would be a database
DEMO_PRODUCTS = {
    "TRP-001": Product(
        id="prod-001",
        sku="TRP-001",
        name="Trail Runner Pro",
        description="Lightweight hiking shoe for day hikes and trail running",
        category=ProductCategory.FOOTWEAR,
        price=149.99,
        cost=65.00,
        quantity=45,
        reorder_point=15,
        status=StockStatus.IN_STOCK,
        location="Warehouse A - Section 12",
    ),
    "SHB-002": Product(
        id="prod-002",
        sku="SHB-002",
        name="Summit Hiking Boot",
        description="Heavy-duty hiking boot for challenging terrain",
        category=ProductCategory.FOOTWEAR,
        price=219.99,
        cost=95.00,
        quantity=12,
        reorder_point=20,
        status=StockStatus.LOW_STOCK,
        location="Warehouse A - Section 12",
    ),
    "AT4-003": Product(
        id="prod-003",
        sku="AT4-003",
        name="Alpine Tent 4P",
        description="4-person tent rated for alpine conditions",
        category=ProductCategory.CAMPING,
        price=449.99,
        cost=180.00,
        quantity=28,
        reorder_point=10,
        status=StockStatus.IN_STOCK,
        location="Warehouse B - Section 5",
    ),
    "EPB-004": Product(
        id="prod-004",
        sku="EPB-004",
        name="Explorer Pro Backpack 65L",
        description="Large capacity backpack for multi-day expeditions",
        category=ProductCategory.EQUIPMENT,
        price=299.99,
        cost=120.00,
        quantity=35,
        reorder_point=15,
        status=StockStatus.IN_STOCK,
        location="Warehouse A - Section 8",
    ),
    "MWJ-005": Product(
        id="prod-005",
        sku="MWJ-005",
        name="Mountain Weatherproof Jacket",
        description="3-layer waterproof breathable shell jacket",
        category=ProductCategory.APPAREL,
        price=329.99,
        cost=140.00,
        quantity=0,
        reorder_point=25,
        status=StockStatus.OUT_OF_STOCK,
        location="Warehouse A - Section 3",
    ),
    "TSP-006": Product(
        id="prod-006",
        sku="TSP-006",
        name="Trekking Poles Set",
        description="Carbon fiber adjustable trekking poles (pair)",
        category=ProductCategory.EQUIPMENT,
        price=129.99,
        cost=45.00,
        quantity=72,
        reorder_point=30,
        status=StockStatus.IN_STOCK,
        location="Warehouse A - Section 15",
    ),
    "HSL-007": Product(
        id="prod-007",
        sku="HSL-007",
        name="Headlamp Summit LED",
        description="Rechargeable 800-lumen headlamp",
        category=ProductCategory.ACCESSORIES,
        price=79.99,
        cost=28.00,
        quantity=58,
        reorder_point=25,
        status=StockStatus.IN_STOCK,
        location="Warehouse A - Section 20",
    ),
    "DSB-008": Product(
        id="prod-008",
        sku="DSB-008",
        name="Down Sleeping Bag -20F",
        description="Ultra-warm down sleeping bag rated to -20F",
        category=ProductCategory.CAMPING,
        price=399.99,
        cost=160.00,
        quantity=18,
        reorder_point=12,
        status=StockStatus.IN_STOCK,
        location="Warehouse B - Section 7",
    ),
    "CFS-009": Product(
        id="prod-009",
        sku="CFS-009",
        name="Camp Fuel Stove Pro",
        description="Compact backpacking stove with piezo ignition",
        category=ProductCategory.CAMPING,
        price=89.99,
        cost=32.00,
        quantity=45,
        reorder_point=20,
        status=StockStatus.IN_STOCK,
        location="Warehouse B - Section 10",
    ),
    "HGP-010": Product(
        id="prod-010",
        sku="HGP-010",
        name="Hiking Gloves Pro",
        description="Touchscreen-compatible insulated gloves",
        category=ProductCategory.ACCESSORIES,
        price=49.99,
        cost=18.00,
        quantity=95,
        reorder_point=40,
        status=StockStatus.IN_STOCK,
        location="Warehouse A - Section 4",
    ),
}

# Demo alerts
DEMO_ALERTS: List[InventoryAlert] = [
    InventoryAlert(
        id="alert-001",
        product_id="prod-002",
        product_name="Summit Hiking Boot",
        sku="SHB-002",
        alert_type="low_stock",
        current_quantity=12,
        threshold=20,
    ),
    InventoryAlert(
        id="alert-002",
        product_id="prod-005",
        product_name="Mountain Weatherproof Jacket",
        sku="MWJ-005",
        alert_type="out_of_stock",
        current_quantity=0,
        threshold=25,
    ),
]


class InventoryTools:
    """MCP Tools for Inventory management"""

    def __init__(self, user_scopes: Optional[List[str]] = None):
        self.user_scopes = user_scopes or ["inventory:read", "inventory:write", "inventory:alert"]
        self._products = DEMO_PRODUCTS.copy()
        self._alerts = DEMO_ALERTS.copy()

    def _has_scope(self, required_scope: str) -> bool:
        """Check if user has required scope"""
        return required_scope in self.user_scopes

    async def _execute_tool(
        self,
        tool_name: str,
        func,
        required_scope: Optional[str] = None,
        **kwargs,
    ) -> ToolCall:
        """Execute a tool and return standardized result"""
        tool_id = f"inv-{tool_name}-{int(time.time() * 1000)}"
        start_time = time.time()

        # Check scope if required
        if required_scope and not self._has_scope(required_scope):
            return ToolCall(
                id=tool_id,
                name=f"inventory.{tool_name}",
                status=ToolCallStatus.ERROR,
                arguments=kwargs,
                error=f"Access denied: requires scope '{required_scope}'",
                duration=0,
            )

        try:
            result = await func(**kwargs) if callable(func) else func
            duration = int((time.time() - start_time) * 1000)

            return ToolCall(
                id=tool_id,
                name=f"inventory.{tool_name}",
                status=ToolCallStatus.COMPLETED,
                arguments=kwargs,
                result=result,
                duration=duration,
            )
        except Exception as e:
            logger.error(f"Inventory tool error: {tool_name}", error=str(e))
            return ToolCall(
                id=tool_id,
                name=f"inventory.{tool_name}",
                status=ToolCallStatus.ERROR,
                arguments=kwargs,
                error=str(e),
                duration=int((time.time() - start_time) * 1000),
            )

    # === STOCK CHECKING TOOLS ===

    async def check_stock(
        self,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ToolCall:
        """Check stock levels for products"""

        async def _execute():
            products = list(self._products.values())

            # Apply filters
            if sku:
                products = [p for p in products if p.sku == sku]
            if category:
                products = [p for p in products if p.category.value == category.lower()]
            if status:
                products = [p for p in products if p.status.value == status.lower()]

            result = [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "quantity": p.quantity,
                    "reorder_point": p.reorder_point,
                    "status": p.status.value,
                    "location": p.location,
                    "category": p.category.value,
                }
                for p in products
            ]

            return {
                "products": result,
                "total_count": len(result),
            }

        return await self._execute_tool(
            "check_stock",
            _execute,
            required_scope="inventory:read",
            sku=sku,
            category=category,
            status=status,
        )

    async def get_product_details(self, sku: str) -> ToolCall:
        """Get detailed information about a specific product"""

        async def _execute():
            product = self._products.get(sku)
            if not product:
                return {"error": "Product not found", "sku": sku}

            return {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "category": product.category.value,
                "price": product.price,
                "cost": product.cost,
                "margin": round((product.price - product.cost) / product.price * 100, 1),
                "quantity": product.quantity,
                "reorder_point": product.reorder_point,
                "status": product.status.value,
                "location": product.location,
                "last_updated": product.last_updated.isoformat(),
            }

        return await self._execute_tool(
            "get_product_details",
            _execute,
            required_scope="inventory:read",
            sku=sku,
        )

    async def search_products(
        self,
        query: str,
        limit: int = 20,
    ) -> ToolCall:
        """Search products by name or description"""

        async def _execute():
            query_lower = query.lower()
            matches = [
                p for p in self._products.values()
                if query_lower in p.name.lower() or query_lower in (p.description or "").lower()
            ][:limit]

            return {
                "products": [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "category": p.category.value,
                        "quantity": p.quantity,
                        "price": p.price,
                        "status": p.status.value,
                    }
                    for p in matches
                ],
                "total_matches": len(matches),
            }

        return await self._execute_tool(
            "search_products",
            _execute,
            required_scope="inventory:read",
            query=query,
            limit=limit,
        )

    # === STOCK UPDATE TOOLS ===

    async def update_stock(
        self,
        sku: str,
        quantity_change: int,
        reason: Optional[str] = None,
    ) -> ToolCall:
        """Update stock quantity for a product"""

        async def _execute():
            product = self._products.get(sku)
            if not product:
                return {"error": "Product not found", "sku": sku}

            old_quantity = product.quantity
            new_quantity = max(0, product.quantity + quantity_change)

            # Update the product
            product.quantity = new_quantity
            product.last_updated = datetime.utcnow()

            # Update status
            if new_quantity == 0:
                product.status = StockStatus.OUT_OF_STOCK
            elif new_quantity < product.reorder_point:
                product.status = StockStatus.LOW_STOCK
            else:
                product.status = StockStatus.IN_STOCK

            return {
                "success": True,
                "sku": sku,
                "product_name": product.name,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "change": quantity_change,
                "new_status": product.status.value,
                "reason": reason,
                "timestamp": product.last_updated.isoformat(),
            }

        return await self._execute_tool(
            "update_stock",
            _execute,
            required_scope="inventory:write",
            sku=sku,
            quantity_change=quantity_change,
            reason=reason,
        )

    async def bulk_stock_update(
        self,
        updates: List[dict],
    ) -> ToolCall:
        """Bulk update stock for multiple products"""

        async def _execute():
            results = []
            for update in updates:
                sku = update.get("sku")
                change = update.get("quantity_change", 0)
                reason = update.get("reason")

                product = self._products.get(sku)
                if not product:
                    results.append({"sku": sku, "success": False, "error": "Product not found"})
                    continue

                old_qty = product.quantity
                new_qty = max(0, product.quantity + change)
                product.quantity = new_qty
                product.last_updated = datetime.utcnow()

                # Update status
                if new_qty == 0:
                    product.status = StockStatus.OUT_OF_STOCK
                elif new_qty < product.reorder_point:
                    product.status = StockStatus.LOW_STOCK
                else:
                    product.status = StockStatus.IN_STOCK

                results.append({
                    "sku": sku,
                    "success": True,
                    "old_quantity": old_qty,
                    "new_quantity": new_qty,
                })

            successful = sum(1 for r in results if r.get("success"))
            return {
                "results": results,
                "total_updated": successful,
                "total_failed": len(results) - successful,
            }

        return await self._execute_tool(
            "bulk_stock_update",
            _execute,
            required_scope="inventory:write",
            updates=updates,
        )

    async def set_reorder_point(
        self,
        sku: str,
        reorder_point: int,
    ) -> ToolCall:
        """Set the reorder point for a product"""

        async def _execute():
            product = self._products.get(sku)
            if not product:
                return {"error": "Product not found", "sku": sku}

            old_point = product.reorder_point
            product.reorder_point = reorder_point
            product.last_updated = datetime.utcnow()

            # Update status if needed
            if product.quantity > 0 and product.quantity < reorder_point:
                product.status = StockStatus.LOW_STOCK

            return {
                "success": True,
                "sku": sku,
                "product_name": product.name,
                "old_reorder_point": old_point,
                "new_reorder_point": reorder_point,
            }

        return await self._execute_tool(
            "set_reorder_point",
            _execute,
            required_scope="inventory:write",
            sku=sku,
            reorder_point=reorder_point,
        )

    # === ALERT TOOLS ===

    async def get_alerts(
        self,
        alert_type: Optional[str] = None,
    ) -> ToolCall:
        """Get inventory alerts"""

        async def _execute():
            alerts = self._alerts
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]

            return {
                "alerts": [
                    {
                        "id": a.id,
                        "product_name": a.product_name,
                        "sku": a.sku,
                        "alert_type": a.alert_type,
                        "current_quantity": a.current_quantity,
                        "threshold": a.threshold,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in alerts
                ],
                "total_count": len(alerts),
            }

        return await self._execute_tool(
            "get_alerts",
            _execute,
            required_scope="inventory:alert",
            alert_type=alert_type,
        )

    async def create_alert(
        self,
        sku: str,
        alert_type: str,
        threshold: int,
    ) -> ToolCall:
        """Create a new inventory alert"""

        async def _execute():
            product = self._products.get(sku)
            if not product:
                return {"error": "Product not found", "sku": sku}

            alert = InventoryAlert(
                id=f"alert-{uuid.uuid4().hex[:8]}",
                product_id=product.id,
                product_name=product.name,
                sku=sku,
                alert_type=alert_type,
                current_quantity=product.quantity,
                threshold=threshold,
            )

            self._alerts.append(alert)

            return {
                "success": True,
                "alert_id": alert.id,
                "sku": sku,
                "alert_type": alert_type,
                "threshold": threshold,
            }

        return await self._execute_tool(
            "create_alert",
            _execute,
            required_scope="inventory:alert",
            sku=sku,
            alert_type=alert_type,
            threshold=threshold,
        )

    async def dismiss_alert(self, alert_id: str) -> ToolCall:
        """Dismiss an inventory alert"""

        async def _execute():
            for i, alert in enumerate(self._alerts):
                if alert.id == alert_id:
                    self._alerts.pop(i)
                    return {"success": True, "alert_id": alert_id}

            return {"error": "Alert not found", "alert_id": alert_id}

        return await self._execute_tool(
            "dismiss_alert",
            _execute,
            required_scope="inventory:alert",
            alert_id=alert_id,
        )

    # === ANALYTICS TOOLS ===

    async def get_stock_summary(self) -> ToolCall:
        """Get overall inventory summary"""

        async def _execute():
            products = list(self._products.values())

            total_value = sum(p.price * p.quantity for p in products)
            low_stock = sum(1 for p in products if p.status == StockStatus.LOW_STOCK)
            out_of_stock = sum(1 for p in products if p.status == StockStatus.OUT_OF_STOCK)

            # Category breakdown
            categories = {}
            for p in products:
                cat = p.category.value
                if cat not in categories:
                    categories[cat] = {"count": 0, "value": 0, "quantity": 0}
                categories[cat]["count"] += 1
                categories[cat]["value"] += p.price * p.quantity
                categories[cat]["quantity"] += p.quantity

            return {
                "total_products": len(products),
                "total_inventory_value": round(total_value, 2),
                "total_units": sum(p.quantity for p in products),
                "low_stock_count": low_stock,
                "out_of_stock_count": out_of_stock,
                "in_stock_count": len(products) - low_stock - out_of_stock,
                "categories": categories,
                "active_alerts": len(self._alerts),
            }

        return await self._execute_tool(
            "get_stock_summary",
            _execute,
            required_scope="inventory:read",
        )

    async def get_low_stock_report(self) -> ToolCall:
        """Get report of all low stock and out of stock items"""

        async def _execute():
            low_stock_items = [
                p for p in self._products.values()
                if p.status in [StockStatus.LOW_STOCK, StockStatus.OUT_OF_STOCK]
            ]

            return {
                "items": [
                    {
                        "sku": p.sku,
                        "name": p.name,
                        "category": p.category.value,
                        "current_quantity": p.quantity,
                        "reorder_point": p.reorder_point,
                        "shortage": p.reorder_point - p.quantity,
                        "status": p.status.value,
                        "estimated_reorder_cost": (p.reorder_point - p.quantity) * p.cost if p.cost else None,
                    }
                    for p in sorted(low_stock_items, key=lambda x: x.quantity)
                ],
                "total_items_needing_reorder": len(low_stock_items),
            }

        return await self._execute_tool(
            "get_low_stock_report",
            _execute,
            required_scope="inventory:read",
        )

    async def get_category_breakdown(self) -> ToolCall:
        """Get inventory breakdown by category"""

        async def _execute():
            categories = {}

            for p in self._products.values():
                cat = p.category.value
                if cat not in categories:
                    categories[cat] = {
                        "product_count": 0,
                        "total_units": 0,
                        "total_value": 0,
                        "low_stock_count": 0,
                        "avg_price": 0,
                    }

                categories[cat]["product_count"] += 1
                categories[cat]["total_units"] += p.quantity
                categories[cat]["total_value"] += p.price * p.quantity
                if p.status == StockStatus.LOW_STOCK:
                    categories[cat]["low_stock_count"] += 1

            # Calculate averages
            for cat in categories:
                if categories[cat]["product_count"] > 0:
                    categories[cat]["avg_price"] = round(
                        categories[cat]["total_value"] / max(categories[cat]["total_units"], 1),
                        2,
                    )
                categories[cat]["total_value"] = round(categories[cat]["total_value"], 2)

            return {"categories": categories}

        return await self._execute_tool(
            "get_category_breakdown",
            _execute,
            required_scope="inventory:read",
        )


    # === DIRECT ACCESS METHODS (Synchronous, for orchestrator) ===

    def list_products(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Product]:
        """Get list of products (synchronous)"""
        products = list(self._products.values())

        if category:
            products = [p for p in products if p.category.value == category]
        if status:
            products = [p for p in products if p.status.value == status]

        return products

    def get_product(self, sku: str) -> Optional[Product]:
        """Get a single product by SKU (synchronous)"""
        return self._products.get(sku)

    def update_stock_sync(
        self,
        sku: str,
        quantity_change: int,
        reason: Optional[str] = None,
    ) -> dict:
        """Update stock quantity (synchronous)"""
        product = self._products.get(sku)
        if not product:
            return {"error": "Product not found", "sku": sku}

        old_quantity = product.quantity
        new_quantity = max(0, product.quantity + quantity_change)

        product.quantity = new_quantity
        product.last_updated = datetime.utcnow()

        if new_quantity == 0:
            product.status = StockStatus.OUT_OF_STOCK
        elif new_quantity < product.reorder_point:
            product.status = StockStatus.LOW_STOCK
        else:
            product.status = StockStatus.IN_STOCK

        return {
            "success": True,
            "sku": sku,
            "product_name": product.name,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "change": quantity_change,
            "new_status": product.status.value,
            "reason": reason,
        }

    def check_low_stock(self, threshold: int = 15) -> dict:
        """Check for low stock items (synchronous)"""
        low_stock_items = [
            p for p in self._products.values()
            if p.quantity < threshold
        ]

        return {
            "items": [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "quantity": p.quantity,
                    "threshold": threshold,
                    "status": p.status.value,
                }
                for p in sorted(low_stock_items, key=lambda x: x.quantity)
            ],
            "count": len(low_stock_items),
            "threshold": threshold,
        }

    def create_reorder(self, sku: str, quantity: int) -> dict:
        """Create a reorder request (synchronous)"""
        product = self._products.get(sku)
        if not product:
            return {"error": "Product not found", "sku": sku}

        return {
            "success": True,
            "reorder_id": f"RO-{uuid.uuid4().hex[:8].upper()}",
            "sku": sku,
            "product_name": product.name,
            "quantity": quantity,
            "estimated_cost": quantity * (product.cost or product.price * 0.5),
            "status": "pending",
        }

    def get_inventory_summary(self) -> dict:
        """Get inventory summary (synchronous)"""
        products = list(self._products.values())

        total_value = sum(p.price * p.quantity for p in products)
        low_stock = sum(1 for p in products if p.status == StockStatus.LOW_STOCK)
        out_of_stock = sum(1 for p in products if p.status == StockStatus.OUT_OF_STOCK)

        return {
            "total_products": len(products),
            "total_value": round(total_value, 2),
            "total_units": sum(p.quantity for p in products),
            "low_stock_count": low_stock,
            "out_of_stock_count": out_of_stock,
            "in_stock_count": len(products) - low_stock - out_of_stock,
        }

    def get_alerts(self) -> List[dict]:
        """Get active alerts (synchronous)"""
        return [
            {
                "id": a.id,
                "product_name": a.product_name,
                "sku": a.sku,
                "alert_type": a.alert_type,
                "current_quantity": a.current_quantity,
                "threshold": a.threshold,
                "severity": "high" if a.current_quantity == 0 else "medium",
                "acknowledged": False,
            }
            for a in self._alerts
        ]

    def get_stock_movements(self, sku: str) -> List[dict]:
        """Get stock movement history (synchronous) - returns demo data"""
        product = self._products.get(sku)
        if not product:
            return []

        # Return demo movement data
        return [
            {
                "id": f"mov-{i}",
                "sku": sku,
                "type": "received" if i % 2 == 0 else "sold",
                "quantity": 10 if i % 2 == 0 else -5,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Demo movement data",
            }
            for i in range(5)
        ]


# Global instance for direct tool access (used by orchestrator)
inventory_tools = InventoryTools()
