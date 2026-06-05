from fastapi.testclient import TestClient

from database import repository
from main import app

client = TestClient(app)


def setup_function() -> None:
    repository.clear()


def sample_order() -> dict[str, object]:
    return {
        "customer_name": "Ananya Sharma",
        "product_name": "Wireless Mouse",
        "quantity": 2,
        "price": 1499.99,
        "status": "pending",
    }


def create_sample_order() -> dict[str, object]:
    response = client.post("/orders", json=sample_order())
    assert response.status_code == 201
    return response.json()


def test_create_order_returns_created_order() -> None:
    response = client.post("/orders", json=sample_order())

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["customer_name"] == "Ananya Sharma"


def test_create_order_rejects_invalid_quantity() -> None:
    payload = sample_order()
    payload["quantity"] = 0

    response = client.post("/orders", json=payload)

    assert response.status_code == 422


def test_list_orders_returns_empty_list_initially() -> None:
    response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_list_orders_returns_created_orders() -> None:
    order = create_sample_order()

    response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == [order]


def test_get_order_by_id_returns_order() -> None:
    order = create_sample_order()

    response = client.get(f"/orders/{order['id']}")

    assert response.status_code == 200
    assert response.json() == order


def test_get_missing_order_returns_404() -> None:
    response = client.get("/orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_update_order_changes_given_fields() -> None:
    order = create_sample_order()

    response = client.put(
        f"/orders/{order['id']}",
        json={"status": "shipped", "quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "shipped"
    assert response.json()["quantity"] == 3
    assert response.json()["product_name"] == "Wireless Mouse"


def test_update_missing_order_returns_404() -> None:
    response = client.put("/orders/999", json={"status": "cancelled"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_patch_order_changes_only_given_fields() -> None:
    order = create_sample_order()

    response = client.patch(
        f"/orders/{order['id']}",
        json={"status": "processing"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert response.json()["quantity"] == 2
    assert response.json()["product_name"] == "Wireless Mouse"


def test_patch_missing_order_returns_404() -> None:
    response = client.patch("/orders/999", json={"status": "cancelled"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_delete_order_removes_order() -> None:
    order = create_sample_order()

    delete_response = client.delete(f"/orders/{order['id']}")
    get_response = client.get(f"/orders/{order['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_missing_order_returns_404() -> None:
    response = client.delete("/orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
