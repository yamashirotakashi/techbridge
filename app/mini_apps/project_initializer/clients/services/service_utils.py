"""Service Utilities - 共通ユーティリティ関数"""
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

class ServiceUtils:
    """サービス層で使用する共通ユーティリティ"""
    
    _executor = None
    
    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """共有ThreadPoolExecutorを取得
        
        Returns:
            ThreadPoolExecutor インスタンス
        """
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(max_workers=5)
        return cls._executor
    
    @classmethod
    async def run_in_executor(cls, func: Callable, *args, **kwargs) -> Any:
        """同期関数を非同期実行
        
        Args:
            func: 実行する関数
            *args: 位置引数
            **kwargs: キーワード引数
            
        Returns:
            関数の実行結果
        """
        executor = cls.get_executor()
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                executor, 
                lambda: func(*args, **kwargs)
            )
            return result
        except Exception as e:
            logger.error(f"Error in executor: {e}")
            raise
    
    @classmethod
    def cleanup(cls):
        """リソースのクリーンアップ"""
        if cls._executor:
            cls._executor.shutdown(wait=True)
            cls._executor = None
            logger.info("Executor cleaned up")