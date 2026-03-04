from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class Account(BaseModel):
    account_id: str = Field(..., description="Legacy account identifier")
    customer_name: str
    branch_code: str
    account_type: str
    balance: Decimal
    currency: str
    status: str


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    posted_at: datetime
    amount: Decimal
    currency: str
    description: str
    direction: str


class HealthResponse(BaseModel):
    status: str
    legacy_source: str
    loaded_accounts: int
    loaded_transactions: int


class AccountSummary(BaseModel):
    account_id: str
    customer_name: str
    balance: Decimal
    currency: str
    last_updated: datetime


class AccountStatusInfo(BaseModel):
    account_id: str
    status: str
    status_reason: str
    regulatory_note: str
    inactivity_threshold_years: int | None = None
    last_customer_activity_at: datetime | None = None
    review_due_at: datetime | None = None


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
