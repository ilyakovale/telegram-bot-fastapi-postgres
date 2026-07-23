import httpx
from config import ORDER_SERVICE_URL

async def create_order(chat_id: int, order_data: dict) -> dict:
    """
    Пример создания заказа через микросервис заказов.
    Ожидаемая структура order_data:
    {
        "date": "YYYY-MM-DD",
        "last_day_before_registration": "YYYY-MM-DD",
        "products": [{"product_name": "...", "quantity": 1, "unit_price": 1.0}, ...]
    }
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/order/create",
                json={"chat_id": chat_id, **order_data},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис заказов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def get_orders():
    """Получить список всех заказов."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/orders", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис заказов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def delete_order(order_date: str):
    """Удалить заказ по дате (YYYY-MM-DD)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{ORDER_SERVICE_URL}/order/{order_date}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис заказов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}