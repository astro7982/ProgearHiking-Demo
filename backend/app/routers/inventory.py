"""
Inventory Router

Direct inventory management endpoints for product and stock operations.
These endpoints use Okta XAA for authorization (Custom Authorization Server).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import structlog

from app.auth.okta_auth import get_current_user, get_id_token, okta_auth
from app.models.schemas import (
    UserInfo,
    Product,
    ProductCategory,
    StockStatus,
    StockMovement,
    MovementType,
    InventoryAlert,
    AlertSeverity,
)
from app.tools.inventory_tools import inventory_tools
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/products", response_model=List[Product])
async def list_products(
    category: Optional[ProductCategory] = None,
    status: Optional[StockStatus] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    user: UserInfo = Depends(get_current_user),
):
    """
    List all products with optional filtering.

    Requires: inventory:read scope
    """
    logger.info(
        "Listing products",
        user_sub=user.sub,
        category=category,
        status=status,
        search=search,
    )

    try:
        # In production, perform XAA token exchange here
        # For demo, use inventory tools directly
        products = inventory_tools.list_products(
            category=category.value if category else None,
            status=status.value if status else None,
        )

        # Apply search filter
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if search_lower in p.name.lower() or search_lower in p.sku.lower()
            ]

        return products[:limit]

    except Exception as e:
        logger.error("Failed to list products", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve products")


@router.get("/products/{sku}", response_model=Product)
async def get_product(
    sku: str,
    user: UserInfo = Depends(get_current_user),
):
    """
    Get detailed product information by SKU.

    Requires: inventory:read scope
    """
    logger.info("Getting product", user_sub=user.sub, sku=sku)

    product = inventory_tools.get_product(sku)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {sku} not found")

    return product


@router.post("/products/{sku}/stock")
async def update_stock(
    sku: str,
    quantity_change: int,
    reason: str,
    movement_type: MovementType = MovementType.ADJUSTMENT,
    user: UserInfo = Depends(get_current_user),
):
    """
    Update product stock level.

    Requires: inventory:write scope

    - quantity_change: Positive to add stock, negative to remove
    - reason: Description of why stock is being changed
    - movement_type: Type of movement (RECEIVED, SOLD, RETURNED, ADJUSTMENT, TRANSFER)
    """
    logger.info(
        "Updating stock",
        user_sub=user.sub,
        sku=sku,
        quantity_change=quantity_change,
        reason=reason,
    )

    try:
        result = inventory_tools.update_stock(
            sku=sku,
            quantity_change=quantity_change,
            reason=reason,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update stock", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update stock")


@router.post("/products/{sku}/reorder")
async def create_reorder(
    sku: str,
    quantity: int = Query(gt=0),
    user: UserInfo = Depends(get_current_user),
):
    """
    Create a reorder request for a product.

    Requires: inventory:write scope
    """
    logger.info(
        "Creating reorder",
        user_sub=user.sub,
        sku=sku,
        quantity=quantity,
    )

    try:
        result = inventory_tools.create_reorder(sku=sku, quantity=quantity)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create reorder", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create reorder")


@router.get("/products/{sku}/movements", response_model=List[StockMovement])
async def get_stock_movements(
    sku: str,
    limit: int = Query(default=20, le=100),
    user: UserInfo = Depends(get_current_user),
):
    """
    Get stock movement history for a product.

    Requires: inventory:read scope
    """
    logger.info("Getting stock movements", user_sub=user.sub, sku=sku)

    movements = inventory_tools.get_stock_movements(sku)
    return movements[:limit]


@router.get("/alerts", response_model=List[InventoryAlert])
async def get_inventory_alerts(
    severity: Optional[AlertSeverity] = None,
    acknowledged: Optional[bool] = None,
    user: UserInfo = Depends(get_current_user),
):
    """
    Get inventory alerts (low stock, out of stock, etc.).

    Requires: inventory:alert scope
    """
    logger.info(
        "Getting inventory alerts",
        user_sub=user.sub,
        severity=severity,
        acknowledged=acknowledged,
    )

    try:
        alerts = inventory_tools.get_alerts()

        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity.value]

        # Filter by acknowledged status
        if acknowledged is not None:
            alerts = [a for a in alerts if a.get("acknowledged") == acknowledged]

        return alerts

    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """
    Acknowledge an inventory alert.

    Requires: inventory:alert scope
    """
    logger.info("Acknowledging alert", user_sub=user.sub, alert_id=alert_id)

    # In production, update the alert in the database
    return {
        "success": True,
        "alert_id": alert_id,
        "acknowledged_by": user.email,
        "message": "Alert acknowledged",
    }


@router.get("/analytics/summary")
async def get_inventory_summary(
    user: UserInfo = Depends(get_current_user),
):
    """
    Get inventory analytics summary.

    Requires: inventory:read scope
    """
    logger.info("Getting inventory summary", user_sub=user.sub)

    try:
        summary = inventory_tools.get_inventory_summary()
        return summary

    except Exception as e:
        logger.error("Failed to get inventory summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


@router.get("/analytics/category/{category}")
async def get_category_analytics(
    category: ProductCategory,
    user: UserInfo = Depends(get_current_user),
):
    """
    Get analytics for a specific product category.

    Requires: inventory:read scope
    """
    logger.info(
        "Getting category analytics",
        user_sub=user.sub,
        category=category.value,
    )

    try:
        products = inventory_tools.list_products(category=category.value)

        total_value = sum(p.price * p.quantity for p in products)
        total_units = sum(p.quantity for p in products)
        avg_price = total_value / total_units if total_units > 0 else 0

        return {
            "category": category.value,
            "product_count": len(products),
            "total_units": total_units,
            "total_value": round(total_value, 2),
            "average_price": round(avg_price, 2),
            "products": [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "quantity": p.quantity,
                    "value": round(p.price * p.quantity, 2),
                }
                for p in products
            ],
        }

    except Exception as e:
        logger.error("Failed to get category analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.get("/analytics/low-stock")
async def get_low_stock_report(
    threshold: int = Query(default=15, ge=1),
    user: UserInfo = Depends(get_current_user),
):
    """
    Get report of products below stock threshold.

    Requires: inventory:alert scope
    """
    logger.info(
        "Getting low stock report",
        user_sub=user.sub,
        threshold=threshold,
    )

    try:
        result = inventory_tools.check_low_stock(threshold=threshold)
        return result

    except Exception as e:
        logger.error("Failed to get low stock report", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.post("/bulk/receive")
async def bulk_receive_inventory(
    items: List[dict],
    user: UserInfo = Depends(get_current_user),
):
    """
    Bulk receive inventory from shipment.

    Requires: inventory:write scope

    items: List of {"sku": "...", "quantity": N}
    """
    logger.info(
        "Bulk receiving inventory",
        user_sub=user.sub,
        item_count=len(items),
    )

    results = []
    for item in items:
        try:
            result = inventory_tools.update_stock(
                sku=item["sku"],
                quantity_change=item["quantity"],
                reason=f"Bulk shipment received by {user.email}",
            )
            results.append({
                "sku": item["sku"],
                "success": "error" not in result,
                "result": result,
            })
        except Exception as e:
            results.append({
                "sku": item["sku"],
                "success": False,
                "error": str(e),
            })

    successful = sum(1 for r in results if r["success"])
    return {
        "total_items": len(items),
        "successful": successful,
        "failed": len(items) - successful,
        "results": results,
    }


@router.get("/xaa/status")
async def get_xaa_status(
    id_token: str = Depends(get_id_token),
    user: UserInfo = Depends(get_current_user),
):
    """
    Check XAA token exchange status for inventory access.

    This endpoint demonstrates the Okta ID-JAG flow for inventory authorization.
    """
    logger.info("Checking XAA status", user_sub=user.sub)

    try:
        # Check if we can perform ID-JAG exchange
        if not settings.inventory_auth_server_id:
            return {
                "xaa_enabled": False,
                "reason": "Inventory auth server not configured",
                "fallback": "Using demo mode with direct access",
            }

        # In production, attempt the ID-JAG exchange here
        # id_jag = await okta_auth.get_id_jag(id_token)
        # access_token = await okta_auth.exchange_id_jag(
        #     id_jag,
        #     settings.inventory_auth_server_id,
        #     ["inventory:read", "inventory:write"]
        # )

        return {
            "xaa_enabled": True,
            "auth_server_id": settings.inventory_auth_server_id,
            "available_scopes": [
                "inventory:read",
                "inventory:write",
                "inventory:alert",
            ],
            "user": user.email,
            "message": "XAA token exchange available",
        }

    except Exception as e:
        logger.error("XAA status check failed", error=str(e))
        return {
            "xaa_enabled": False,
            "error": str(e),
        }
