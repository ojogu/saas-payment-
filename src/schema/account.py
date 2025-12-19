from pydantic import BaseModel

class Create_Account(BaseModel):
    account_name: str
    account_number: str
    bank: str
    bank_name: str
