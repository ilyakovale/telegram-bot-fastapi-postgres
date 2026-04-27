from pydantic import BaseModel

class AccountMessageRequest(BaseModel):
    chat_id: int
    command: str     

class AccountMessageAnswer(BaseModel):
    chat_id: int
    name: str 
    addres: str
    phone_number: str
