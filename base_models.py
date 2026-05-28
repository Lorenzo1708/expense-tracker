from pydantic import BaseModel


class Profile(BaseModel):
    user_id: str
    created_at: str
    updated_at: str
    name: str
    weekly_budget: float


class Balance(BaseModel):
    user_id: str
    amount: float


class Expense(BaseModel):
    id: str
    user_id: str
    created_at: str
    updated_at: str
    name: str
    cost: float
    date: str
