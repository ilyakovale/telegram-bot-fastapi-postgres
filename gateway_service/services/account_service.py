import httpx
from config import ACCOUNT_SERVICE_URL

async def get_account_info(message, chat_id: int):
    """Запрос данных аккаунта по chat_id."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ACCOUNT_SERVICE_URL}/account_get",
                json={"chat_id": chat_id, "command": "get_info"},
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == "Данные отправлены":
                    await message.answer(
                        f"Данные аккаунта:\n"
                        f"ФИО: {result.get('name')}\n"
                        f"Адрес: {result.get('address')}\n"
                        f"Телефон: {result.get('phone_number')}"
                    )
                else:
                    await message.answer(result.get('status', 'Неизвестный ответ'))
            else:
                await message.answer(f"Ошибка сервиса аккаунтов: {response.status_code}")
        except httpx.TimeoutException:
            await message.answer("Сервис аккаунтов не отвечает")
        except Exception as e:
            await message.answer(f"Ошибка: {str(e)}")

async def set_account_info(message, chat_id: int, name: str, address: str, phone_number: str):
    """Отправка новых данных аккаунта."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ACCOUNT_SERVICE_URL}/account_set",
                json={
                    "chat_id": chat_id,
                    "command": "input_info",
                    "name": name,
                    "address": address,
                    "phone_number": phone_number
                },
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                await message.answer(result.get('status', 'Данные сохранены'))
            else:
                await message.answer(f"Ошибка сохранения: {response.status_code}")
        except httpx.TimeoutException:
            await message.answer("Сервис аккаунтов не отвечает")
        except Exception as e:
            await message.answer(f"Ошибка: {str(e)}")

async def check_account_exists(chat_id: int) -> bool:
    """Проверка существования аккаунта. Возвращает True/False."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ACCOUNT_SERVICE_URL}/account_check",
                json={"chat_id": chat_id},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('exists', False)
            return False
        except Exception:
            return False

async def get_all_accounts(message):
    """Получить список всех аккаунтов (админка)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ACCOUNT_SERVICE_URL}/all_accounts_get",
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                accounts = result.get('accounts', [])
                if not accounts:
                    await message.answer("Аккаунты не найдены")
                    return
                parts = []
                for i, acc in enumerate(accounts):
                    parts.append(
                        f"Аккаунт {i+1}:\n"
                        f"├─ ФИО: {acc.get('name', 'Не указано')}\n"
                        f"├─ Адрес: {acc.get('address', 'Не указано')}\n"
                        f"└─ Телефон: {acc.get('phone_number', 'Не указано')}"
                    )
                text = "\n\n".join(parts)
                if len(text) > 4096:
                    for x in range(0, len(text), 4096):
                        await message.answer(text[x:x+4096])
                else:
                    await message.answer(f"📋 Все аккаунты:\n\n{text}")
            else:
                await message.answer(f"Ошибка: {response.status_code}")
        except httpx.TimeoutException:
            await message.answer("Сервис аккаунтов не отвечает")
        except Exception as e:
            await message.answer(f"Ошибка: {str(e)}")