from pydantic import BaseModel

class AccountMessageRequest(BaseModel):
    chat_id: int
    command: str     

class OrderMessageReques(BaseModel):
    chat_id: int
    command: str
