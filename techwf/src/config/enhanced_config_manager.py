#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge拡張設定管理システム
Phase 4: 外部設定ファイル構造実装 - 統合設定管理

ConfigManager + ConfigValidator + ConfigWatcherの統合システム
リアルタイム設定監視、検証、フォールバック機能を提供
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import logging
import threading
import asyncio

from .config_manager import ConfigManager, get_config_manager
from .config_validator import ConfigValidator, ValidationResult
from .config_watcher import ConfigWatcher, ConfigChange

logger = logging.getLogger(__name__)


class EnhancedConfigManager:
    """
    TechBridge拡張設定管理システム
    
    設定の読み込み、検証、監視、自動修復を一元的に管理
    """
    
    def __init__(self, project_root: Optional[str] = None, auto_start_watching: bool = True):
        """
        拡張設定管理システムの初期化
        
        Args:
            project_root: プロジェクトルートディレクトリ
            auto_start_watching: 自動監視開始フラグ
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        
        # コアコンポーネントの初期化
        self.config_manager = ConfigManager(str(self.project_root))
        self.validator = ConfigValidator(str(self.project_root))
        self.watcher = ConfigWatcher(
            self.config_manager,
            watch_directories=[str(self.project_root / "config")]
        )
        
        # 状態管理
        self.is_initialized = False
        self.validation_enabled = True
        self.auto_repair_enabled = True
        self._lock = threading.RLock()
        
        # イベントコールバック
        self.validation_callbacks: List[Callable[[str, ValidationResult], None]] = []
        self.repair_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # 統計情報
        self.stats = {
            'configs_loaded': 0,
            'validations_performed': 0,
            'auto_repairs_applied': 0,
            'changes_detected': 0,
            'last_validation': None,
            'last_repair': None
        }
        
        # 初期化
        self._setup_callbacks()
        if auto_start_watching:
            self.start_monitoring()
    
    def _setup_callbacks(self):
        """内部コールバックの設定"""
        # 設定変更時の自動検証・修復
        self.watcher.add_change_callback(self._on_config_change)
        self.watcher.add_reload_callback(self._on_config_reload)
    
    def _on_config_change(self, change: ConfigChange):
        """設定変更時の処理"""
        with self._lock:
            self.stats['changes_detected'] += 1
            logger.info(f"設定変更検出: {change.config_name} ({change.change_type})")
            
            if change.change_type != 'deleted' and self.validation_enabled:
                # 自動検証・修復の実行
                self._validate_and_repair(change.config_name)
    
    def _on_config_reload(self, config_name: str):
        """設定再読み込み時の処理"""
        logger.info(f"設定再読み込み完了: {config_name}")
    
    def _validate_and_repair(self, config_name: str) -> bool:
        """設定の検証と自動修復"""
        try:
            # 現在の設定データを取得
            config_data = self.config_manager._configs.get(config_name, {})
            if not config_data:
                logger.warning(f"設定データが見つかりません: {config_name}")
                return False
            
            # 検証実行
            validation_result = self.validator.validate_config(config_name, config_data)
            self.stats['validations_performed'] += 1
            self.stats['last_validation'] = datetime.now()
            
            # 検証コールバック実行
            for callback in self.validation_callbacks:
                try:
                    callback(config_name, validation_result)
                except Exception as e:
                    logger.error(f"検証コールバックエラー: {e}")
            
            # 自動修復が有効で、エラーがある場合
            if self.auto_repair_enabled and not validation_result.is_valid:
                critical_errors = [e for e in validation_result.errors if e.severity == 'critical']
                if critical_errors:
                    logger.warning(f"重大な設定エラーを検出、自動修復を実行: {config_name}")
                    repaired_config = self.validator.apply_fallbacks(config_name, config_data)
                    
                    # 修復された設定をConfigManagerに反映
                    self.config_manager._configs[config_name] = repaired_config
                    self.stats['auto_repairs_applied'] += 1
                    self.stats['last_repair'] = datetime.now()
                    
                    # 修復コールバック実行
                    for callback in self.repair_callbacks:
                        try:
                            callback(config_name, repaired_config)
                        except Exception as e:
                            logger.error(f"修復コールバックエラー: {e}")
                    
                    return True
            
            return validation_result.is_valid
            
        except Exception as e:
            logger.error(f"設定検証・修復エラー {config_name}: {e}")
            return False
    
    def start_monitoring(self):
        """設定監視の開始"""
        try:
            if not self.watcher.is_watching:
                self.watcher.start_watching()
            
            # 初期検証の実行
            self.validate_all_configs()
            self.is_initialized = True
            
            logger.info("拡張設定管理システム開始完了")
            
        except Exception as e:
            logger.error(f"設定監視開始エラー: {e}")
            raise
    
    def stop_monitoring(self):
        """設定監視の停止"""
        try:
            if self.watcher.is_watching:
                self.watcher.stop_watching()
            
            logger.info("拡張設定管理システム停止完了")
            
        except Exception as e:
            logger.error(f"設定監視停止エラー: {e}")
    
    def validate_all_configs(self) -> Dict[str, ValidationResult]:
        """全設定の検証実行"""
        results = {}
        
        for config_name, config_data in self.config_manager._configs.items():
            if config_data:  # 空でない設定のみ検証
                result = self.validator.validate_config(config_name, config_data)
                results[config_name] = result
                
                # 重大エラーがある場合は自動修復
                if self.auto_repair_enabled and not result.is_valid:
                    critical_errors = [e for e in result.errors if e.severity == 'critical']
                    if critical_errors:
                        repaired_config = self.validator.apply_fallbacks(config_name, config_data)
                        self.config_manager._configs[config_name] = repaired_config
        
        self.stats['validations_performed'] += len(results)
        return results
    
    def get(self, key_path: str, default: Any = None, validate: bool = True) -> Any:
        """
        設定値の取得（検証付き）
        
        Args:
            key_path: 設定キーパス
            default: デフォルト値
            validate: 取得時検証フラグ
            
        Returns:
            設定値
        """
        with self._lock:
            value = self.config_manager.get(key_path, default)
            
            if validate and value != default:
                config_name = key_path.split('.')[0]
                if config_name in self.config_manager._configs:
                    self._validate_and_repair(config_name)
                    # 修復後に再取得
                    value = self.config_manager.get(key_path, default)
            
            return value
    
    def get_with_env_override(self, key_path: str, env_var: str, default: Any = None) -> Any:
        """環境変数オーバーライド付き設定取得"""
        return self.config_manager.get_with_env_override(key_path, env_var, default)
    
    def get_theme_config(self, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """テーマ設定の取得"""
        return self.config_manager.get_theme_config(theme_name)
    
    def get_path(self, path_key: str, **format_kwargs) -> str:
        """パス設定の取得とフォーマット"""
        return self.config_manager.get_path(path_key, **format_kwargs)
    
    def get_server_config(self) -> Dict[str, Any]:
        """サーバー設定の取得"""
        return self.config_manager.get_server_config()
    
    def reload_config(self, config_name: Optional[str] = None, force_validation: bool = True):
        """設定の再読み込み"""
        self.config_manager.reload_config(config_name)
        
        if force_validation:
            if config_name:
                self._validate_and_repair(config_name)
            else:
                self.validate_all_configs()
    
    def add_validation_callback(self, callback: Callable[[str, ValidationResult], None]):
        """検証コールバックの追加"""
        self.validation_callbacks.append(callback)
    
    def add_repair_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """修復コールバックの追加"""
        self.repair_callbacks.append(callback)
    
    def enable_validation(self):
        """検証機能の有効化"""
        self.validation_enabled = True
        logger.info("設定検証機能を有効化しました")
    
    def disable_validation(self):
        """検証機能の無効化"""
        self.validation_enabled = False
        logger.info("設定検証機能を無効化しました")
    
    def enable_auto_repair(self):
        """自動修復機能の有効化"""
        self.auto_repair_enabled = True
        logger.info("自動修復機能を有効化しました")
    
    def disable_auto_repair(self):
        """自動修復機能の無効化"""
        self.auto_repair_enabled = False
        logger.info("自動修復機能を無効化しました")
    
    def get_health_status(self) -> Dict[str, Any]:
        """システム健全性状態の取得"""
        validation_results = {}
        for config_name in self.config_manager._configs:
            config_data = self.config_manager._configs[config_name]
            if config_data:
                result = self.validator.validate_config(config_name, config_data)
                validation_results[config_name] = result.is_valid
        
        total_configs = len(validation_results)
        valid_configs = sum(1 for is_valid in validation_results.values() if is_valid)
        
        return {
            'is_healthy': valid_configs == total_configs,
            'total_configs': total_configs,
            'valid_configs': valid_configs,
            'invalid_configs': total_configs - valid_configs,
            'monitoring_active': self.watcher.is_watching,
            'validation_enabled': self.validation_enabled,
            'auto_repair_enabled': self.auto_repair_enabled,
            'stats': self.stats.copy(),
            'config_status': validation_results
        }
    
    def export_system_report(self, output_path: Optional[str] = None) -> str:
        """システム状態レポートの出力"""
        if output_path is None:
            output_path = f"enhanced_config_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        
        # 現在の検証結果を取得
        validation_results = self.validate_all_configs()
        
        report_data = {
            'system_info': {
                'project_root': str(self.project_root),
                'generated_at': datetime.now().isoformat(),
                'monitoring_active': self.watcher.is_watching,
                'validation_enabled': self.validation_enabled,
                'auto_repair_enabled': self.auto_repair_enabled
            },
            'health_status': self.get_health_status(),
            'validation_results': {
                name: {
                    'is_valid': result.is_valid,
                    'error_count': len(result.errors),
                    'warning_count': len(result.warnings),
                    'fallback_count': len(result.fallback_applied)
                }
                for name, result in validation_results.items()
            },
            'recent_changes': [
                {
                    'config_name': change.config_name,
                    'change_type': change.change_type,
                    'timestamp': change.timestamp.isoformat(),
                    'file_path': change.file_path
                }
                for change in self.watcher.get_recent_changes(10)
            ]
        }
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(report_data, file, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"システム状態レポート出力完了: {output_file}")
        return str(output_file)
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        if not self.is_initialized:
            self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.stop_monitoring()


# グローバル拡張設定管理インスタンス
_enhanced_config_manager: Optional[EnhancedConfigManager] = None


def get_enhanced_config_manager(project_root: Optional[str] = None) -> EnhancedConfigManager:
    """グローバル拡張設定管理インスタンスの取得"""
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        _enhanced_config_manager = EnhancedConfigManager(project_root)
    return _enhanced_config_manager


def cleanup_enhanced_config_manager():
    """グローバル拡張設定管理インスタンスのクリーンアップ"""
    global _enhanced_config_manager
    if _enhanced_config_manager:
        _enhanced_config_manager.stop_monitoring()
        _enhanced_config_manager = None


if __name__ == "__main__":
    # 拡張設定管理システムのテスト
    print("=== TechBridge拡張設定管理システム テスト ===")
    
    def on_validation_result(config_name: str, result: ValidationResult):
        """検証結果コールバック"""
        status = "有効" if result.is_valid else "無効"
        print(f"検証結果 {config_name}: {status}")
        if result.errors:
            print(f"  エラー: {len(result.errors)}件")
        if result.warnings:
            print(f"  警告: {len(result.warnings)}件")
    
    def on_auto_repair(config_name: str, repaired_config: Dict[str, Any]):
        """自動修復コールバック"""
        print(f"自動修復実行: {config_name}")
    
    # 拡張設定管理システムの作成
    with EnhancedConfigManager("/mnt/c/Users/tky99/dev/techbridge") as enhanced_manager:
        # コールバック登録
        enhanced_manager.add_validation_callback(on_validation_result)
        enhanced_manager.add_repair_callback(on_auto_repair)
        
        # 設定値の取得テスト
        print(f"デフォルトテーマ: {enhanced_manager.get('theme.default_theme')}")
        print(f"ソケットポート: {enhanced_manager.get('server.socket_server.port')}")
        
        # 健全性状態の確認
        health = enhanced_manager.get_health_status()
        print(f"システム健全性: {'正常' if health['is_healthy'] else '異常'}")
        print(f"有効設定: {health['valid_configs']}/{health['total_configs']}")
        
        # システムレポートの出力
        report_path = enhanced_manager.export_system_report()
        print(f"システムレポート: {report_path}")
        
        print("設定ファイル監視中... (Ctrl+C で終了)")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n終了します...")
    
    print("=== テスト完了 ===")