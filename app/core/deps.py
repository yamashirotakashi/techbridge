"""共通の依存性"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import api_key_auth, auth_service
from app.core.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションを取得"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(token_data: dict = Depends(auth_service.verify_token)) -> dict:
    """現在のユーザーを取得"""
    return token_data


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """APIキーを検証"""
    return await api_key_auth(x_api_key)


async def get_optional_auth(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> Optional[dict]:
    """オプショナル認証（トークンまたはAPIキー）"""
    # APIキーが提供されている場合
    if x_api_key:
        try:
            await api_key_auth(x_api_key)
            return {"type": "api_key", "key": x_api_key}
        except HTTPException:
            pass
    
    # Bearerトークンが提供されている場合
    if authorization and authorization.startswith("Bearer "):
        try:
            from fastapi.security import HTTPAuthorizationCredentials
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=authorization.replace("Bearer ", "")
            )
            token_data = await auth_service.verify_token(credentials)
            return {"type": "bearer", "data": token_data}
        except HTTPException:
            pass
    
    return None