from pydantic import BaseModel

class GetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str     

class SetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str    
    name: str
    address: str
    phone_number: str

