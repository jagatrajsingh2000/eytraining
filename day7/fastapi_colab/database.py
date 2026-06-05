from fastapi import Depends

from models import OrderCreate, OrderResponse, OrderUpdate


class OrderRepository:
    def __init__(self) -> None:
        self._orders: dict[int, OrderResponse] = {}
        self._next_id = 1

    def list_orders(self) -> list[OrderResponse]:
        return list(self._orders.values())

    def get_order(self, order_id: int) -> OrderResponse | None:
        return self._orders.get(order_id)

    def create_order(self, order: OrderCreate) -> OrderResponse:
        order_response = OrderResponse(id=self._next_id, **order.model_dump())
        self._orders[self._next_id] = order_response
        self._next_id += 1
        return order_response

    def update_order(self, order_id: int, order: OrderUpdate) -> OrderResponse | None:
        existing_order = self.get_order(order_id)
        if existing_order is None:
            return None

        update_data = order.model_dump(exclude_unset=True)
        updated_order = existing_order.model_copy(update=update_data)
        self._orders[order_id] = updated_order
        return updated_order

    def delete_order(self, order_id: int) -> bool:
        if order_id not in self._orders:
            return False

        del self._orders[order_id]
        return True

    def clear(self) -> None:
        self._orders.clear()
        self._next_id = 1


repository = OrderRepository()


def get_order_repository() -> OrderRepository:
    return repository


OrderRepositoryDependency = Depends(get_order_repository)
