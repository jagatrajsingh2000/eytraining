# E-Commerce Order Management API

FastAPI project for Day 7 training. It uses an in-memory repository and exposes CRUD endpoints for managing e-commerce orders.

## Project Structure

```text
fastapi_colab/
+-- main.py
+-- models.py
+-- database.py
+-- routers/
|   +-- __init__.py
|   +-- orders.py
+-- tests/
    +-- test_orders.py
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/orders` | Create an order |
| `GET` | `/orders` | List all orders |
| `GET` | `/orders/{order_id}` | Get one order |
| `PUT` | `/orders/{order_id}` | Update an order |
| `PATCH` | `/orders/{order_id}` | Partially update an order |
| `DELETE` | `/orders/{order_id}` | Delete an order |

## Run the API

From the `eytraining/day7/fastapi_colab` folder:

```powershell
uvicorn main:app --reload
```

Open the Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## Example Request

```json
{
  "customer_name": "Ananya Sharma",
  "product_name": "Wireless Mouse",
  "quantity": 2,
  "price": 1499.99,
  "status": "pending"
}
```

## Run Tests

From the `eytraining/day7/fastapi_colab` folder:

```powershell
pytest
```
