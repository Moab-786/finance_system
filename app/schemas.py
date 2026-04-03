from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime, timezone
from app.models import UserRole, TransactionType

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.viewer

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    token: str

class TransactionCreate(BaseModel):
    amount: float = Field(gt=0, le=1_000_000_000)
    type: TransactionType
    category: str = Field(min_length=2, max_length=50)
    date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("date cannot be in the future")
        return value

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0, le=1_000_000_000)
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=50)
    date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_optional_category(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.strip().lower()

    @field_validator("date")
    @classmethod
    def validate_optional_date_not_future(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("date cannot be in the future")
        return value

class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    category: str
    date: datetime
    notes: Optional[str]
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionOut]
    total: int
    skip: int
    limit: int


class TransactionFilters(BaseModel):
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be earlier than or equal to to_date")
        return self