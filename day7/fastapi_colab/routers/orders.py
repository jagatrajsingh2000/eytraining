from fastapi import APIRouter, Depends, HTTPException, status

from database import OrderRepository, get_order_repository
from models import OrderCreate, OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:
    return repository.create_order(order)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    repository: OrderRepository = Depends(get_order_repository),
) -> list[OrderResponse]:
    return repository.list_orders()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:
    order = repository.get_order(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:
    order = repository.update_order(order_id, order_update)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
def patch_order(
    order_id: int,
    order_update: OrderUpdate,
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderResponse:
    order = repository.update_order(order_id, order_update)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    repository: OrderRepository = Depends(get_order_repository),
) -> None:
    deleted = repository.delete_order(order_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
