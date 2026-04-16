from pydantic import BaseModel

class SendMessageRequest(BaseModel):
    chat_id: int  # ID чата (не объект Update)
    text: str     # Текст сообщения
    parse_mode: str = "HTML"  # Режим форматирования