import httpx
from config import ORDER_SERVICE_URL


async def create_order(chat_id: int, order_data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/order_create",
                json={"chat_id": chat_id, **order_data},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return {
                "status": "error",
                "message": f"Ошибка сервиса: {response.status_code}",
            }
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис заказов не отвечает"}
        except httpx.RequestError as e:
            return {"status": "error", "message": f"Ошибка соединения: {e!s}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


async def get_user_orders(chat_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/orders_get",
                json={"chat_id": chat_id},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return {
                "status": "error",
                "message": f"Ошибка сервиса: {response.status_code}",
                "orders": [],
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "Сервис заказов не отвечает",
                "orders": [],
            }
        except httpx.RequestError as e:
            return {
                "status": "error",
                "message": f"Ошибка соединения: {e!s}",
                "orders": [],
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "orders": []}


async def get_all_orders() -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{ORDER_SERVICE_URL}/all_orders_get", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            return {
                "status": "error",
                "message": f"Ошибка сервиса: {response.status_code}",
                "orders": [],
            }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "message": "Сервис заказов не отвечает",
                "orders": [],
            }
        except httpx.RequestError as e:
            return {
                "status": "error",
                "message": f"Ошибка соединения: {e!s}",
                "orders": [],
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "orders": []}


async def delete_order(order_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/order_delete",
                json={"order_id": order_id},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return {
                "status": "error",
                "message": f"Ошибка сервиса: {response.status_code}",
            }
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис заказов не отвечает"}
        except httpx.RequestError as e:
            return {"status": "error", "message": f"Ошибка соединения: {e!s}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


async def get_available_products(order_date: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/products_get",
                json={"order_date": order_date},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("products", [])
            return [
                {"id": 1, "name": "Молоко 1л"},
                {"id": 2, "name": "Творог 200г"},
                {"id": 3, "name": "Сыр 300г"},
            ]
        except (httpx.TimeoutException, httpx.RequestError):
            return [
                {"id": 1, "name": "Молоко 1л"},
                {"id": 2, "name": "Творог 200г"},
                {"id": 3, "name": "Сыр 300г"},
            ]
        except Exception:
            return [
                {"id": 1, "name": "Молоко 1л"},
                {"id": 2, "name": "Творог 200г"},
                {"id": 3, "name": "Сыр 300г"},
            ]


create_order_api = create_order
get_user_orders_api = get_user_orders
get_all_orders_api = get_all_orders
delete_order_api = delete_order
get_available_products_api = get_available_products
