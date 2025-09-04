import logging
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from backend.application.use_cases import (
    CreateOrderUseCase,
    DeleteOrderUseCase,
    GetOrdersUseCase,
    UpdateOrderUseCase,
)
from backend.domain.entities import Order, OrderStatus
from backend.presentation.api.containers import Container

logger = logging.getLogger("conversational_commerce")

router = APIRouter()


@router.get("/{order_id}", response_model=Order)
@inject
async def get_order_by_id(
    order_id: str,
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> Order:
    """Get an order by its ID.

    Args:
        order_id: The order ID to retrieve
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        Order object if found

    Raises:
        HTTPException: If order is not found
    """
    order = await get_orders_use_case.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/user/{user_id}", response_model=List[Order])
@inject
async def get_user_orders(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> List[Order]:
    """Get orders for a specific user.

    Args:
        user_id: The user ID to get orders for
        limit: Maximum number of orders to return
        offset: Number of orders to skip
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        List of Order objects for the user
    """
    return await get_orders_use_case.get_user_orders(user_id, limit, offset)


@router.get("/user/{user_id}/active", response_model=List[Order])
@inject
async def get_user_active_orders(
    user_id: str,
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> List[Order]:
    """Get active orders for a specific user.

    Args:
        user_id: The user ID to get active orders for
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        List of active Order objects for the user
    """
    return await get_orders_use_case.get_user_active_orders(user_id)


@router.get("/status/{status}", response_model=List[Order])
@inject
async def get_orders_by_status(
    status: OrderStatus,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> List[Order]:
    """Get orders by status.

    Args:
        status: The order status to filter by
        limit: Maximum number of orders to return
        offset: Number of orders to skip
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        List of Order objects with the specified status
    """
    return await get_orders_use_case.get_orders_by_status(status, limit, offset)


@router.get("/recent", response_model=List[Order])
@inject
async def get_recent_orders(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of orders to return"),
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> List[Order]:
    """Get recent orders within a specified number of days.

    Args:
        days: Number of days to look back
        limit: Maximum number of orders to return
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        List of recent Order objects
    """
    return await get_orders_use_case.get_recent_orders(days, limit)


@router.get("/user/{user_id}/statistics")
@inject
async def get_user_order_statistics(
    user_id: str,
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> dict:
    """Get order statistics for a specific user.

    Args:
        user_id: The user ID to get statistics for
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        Dictionary containing order statistics for the user
    """
    return await get_orders_use_case.get_user_order_statistics(user_id)


@router.get("/statistics/global")
@inject
async def get_global_order_statistics(
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> dict:
    """Get global order statistics.

    Args:
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        Dictionary containing global order statistics
    """
    return await get_orders_use_case.get_global_order_statistics()


@router.post("/", response_model=Order)
@inject
async def create_order(
    order: Order,
    create_order_use_case: CreateOrderUseCase = Depends(
        Provide[Container.application.create_order_use_case]
    ),
) -> Order:
    """Create a new order.

    Args:
        order: Order object to create
        create_order_use_case: The CreateOrderUseCase for creating orders

    Returns:
        The created Order object
    """
    return await create_order_use_case.execute(order)


@router.put("/{order_id}/status", response_model=Order)
@inject
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    update_order_use_case: UpdateOrderUseCase = Depends(
        Provide[Container.application.update_order_use_case]
    ),
) -> Order:
    """Update the status of an order.

    Args:
        order_id: The order ID to update
        status: The new status
        update_order_use_case: The UpdateOrderUseCase for updating orders

    Returns:
        Updated Order object if found

    Raises:
        HTTPException: If order is not found
    """
    updated_order = await update_order_use_case.update_order_status(order_id, status)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order


@router.put("/{order_id}", response_model=Order)
@inject
async def update_order(
    order_id: str,
    order: Order,
    update_order_use_case: UpdateOrderUseCase = Depends(
        Provide[Container.application.update_order_use_case]
    ),
) -> Order:
    """Update an existing order.

    Args:
        order_id: The order ID to update
        order: The order object with updated information
        update_order_use_case: The UpdateOrderUseCase for updating orders

    Returns:
        Updated Order object if found

    Raises:
        HTTPException: If order is not found
    """
    # Ensure the order_id in the path matches the order object
    order.order_id = order_id
    updated_order = await update_order_use_case.update_order(order)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order


@router.delete("/{order_id}")
@inject
async def delete_order(
    order_id: str,
    delete_order_use_case: DeleteOrderUseCase = Depends(
        Provide[Container.application.delete_order_use_case]
    ),
) -> dict:
    """Delete an order.

    Args:
        order_id: The order ID to delete
        delete_order_use_case: The DeleteOrderUseCase for deleting orders

    Returns:
        Success message

    Raises:
        HTTPException: If order is not found
    """
    success = await delete_order_use_case.execute(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}


@router.post("/ask", response_model=dict)
@inject
async def ask_orders_question(
    question: str,
    user_email: Optional[str] = None,
    order_id: Optional[str] = None,
    additional_details: Optional[str] = None,
    session_id: str = "default",
    model: str = "openai_gpt_4o",
    mode: str = "graph",
    backend_url: Optional[str] = None,
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> dict:
    """Ask questions about orders using the external graph API.

    Args:
        question: The question about orders
        user_email: User's email for filtering orders
        order_id: Specific order ID to focus on
        additional_details: Additional context or details
        session_id: Session identifier
        model: AI model to use
        mode: API mode
        backend_url: External API URL
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        Dictionary containing the API response
    """
    try:
        result = await get_orders_use_case.ask_orders_graph(
            question=question,
            user_email=user_email,
            order_id=order_id,
            additional_details=additional_details,
            session_id=session_id,
            model=model,
            mode=mode,
            backend_url=backend_url
        )
        return result
    except Exception as e:
        logger.error(f"Error in ask_orders_question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing order question: {str(e)}")


@router.get("/graph-data", response_model=List[dict])
@inject
async def get_orders_for_graph(
    user_email: Optional[str] = None,
    order_id: Optional[str] = None,
    get_orders_use_case: GetOrdersUseCase = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
) -> List[dict]:
    """Get orders in a format suitable for the graph API.

    Args:
        user_email: User's email to filter orders
        order_id: Specific order ID to retrieve
        get_orders_use_case: The GetOrdersUseCase for retrieving orders

    Returns:
        List of order dictionaries formatted for graph API
    """
    try:
        orders = await get_orders_use_case.order_service.get_orders_for_graph_api(user_email, order_id)
        return orders
    except Exception as e:
        logger.error(f"Error getting orders for graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")
