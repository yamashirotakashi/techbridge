"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema."""
    
    username: Optional[str] = None


class User(BaseModel):
    """User schema."""
    
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User in database schema."""
    
    hashed_password: str