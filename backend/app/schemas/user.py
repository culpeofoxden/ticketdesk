from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreateByAdmin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole = UserRole.customer
    full_name: str | None = Field(default=None, min_length=2, max_length=255)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
