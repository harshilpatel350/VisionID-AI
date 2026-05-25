from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

class UserOut(ORMBase):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

class MeResponse(UserOut):
    pass
