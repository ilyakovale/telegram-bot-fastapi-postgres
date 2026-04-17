from pydantic import BaseModel

class AccountMessageRequest(BaseModel):
    chat_id: int  # ID чата 
    text: str     # Текст сообщения
    parse_mode: str = "HTML"  # Режим форматирования