"""認証エンドポイント"""

from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.auth import auth_service
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    """トークンレスポンス"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """トークンデータ"""
    username: str | None = None


class User(BaseModel):
    """ユーザーモデル"""
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


# 仮のユーザーデータベース（本番環境では実際のDBを使用）
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@techbridge.example",
        "hashed_password": auth_service.get_password_hash("admin123"),
        "disabled": False,
    },
    "editor": {
        "username": "editor",
        "full_name": "Editor User",
        "email": "editor@techbridge.example",
        "hashed_password": auth_service.get_password_hash("editor123"),
        "disabled": False,
    }
}


def authenticate_user(username: str, password: str) -> User | bool:
    """ユーザーを認証"""
    user_dict = fake_users_db.get(username)
    if not user_dict:
        return False
    if not auth_service.verify_password(password, user_dict["hashed_password"]):
        return False
    return User(**user_dict)


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """ログインしてアクセストークンを取得"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: Dict = Depends(auth_service.verify_token)) -> User:
    """現在のユーザー情報を取得"""
    username = current_user.get("sub")
    user_dict = fake_users_db.get(username)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return User(**user_dict)