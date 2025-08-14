#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge設定システム総合テスト
Phase 5: 設定値検証とフォールバック機構の実装 - システム検証ツール

全設定システムの統合テスト、検証精度確認、フォールバック動作確認
"""

import os
import sys
import yaml
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import tempfile
from dataclasses import dataclass

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
config_src_path = str(project_root / "techwf" / "src")
sys.path.insert(0, config_src_path)

try:
    # 直接インポートでテスト
    from config.config_manager import ConfigManager
    from config.config_validator import ConfigValidator, ValidationResult
    from config.config_watcher import ConfigWatcher
    from config.enhanced_config_manager import EnhancedConfigManager
    from config import create_config_system, NEW_CONFIG_SYSTEM_AVAILABLE
    
    print(f"✅ 設定システムモジュール読み込み成功")
    
except ImportError as e:
    print(f"❌ 設定システムのインポートに失敗しました: {e}")
    print(f"検索パス: {config_src_path}")
    print("依存関係を確認してください:")
    print("pip install watchdog jsonschema pyyaml")
    
    # 個別モジュール存在確認
    config_dir = Path(config_src_path) / "config"
    if config_dir.exists():
        files = list(config_dir.glob("*.py"))
        print(f"発見されたファイル: {[f.name for f in files]}")
    
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """テスト結果情報"""
    test_name: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ConfigSystemTester:
    """設定システム総合テスター"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_results: List[TestResult] = []
        self.temp_dir = None
        
    def setup_test_environment(self):
        """テスト環境の構築"""
        print("🔧 テスト環境構築中...")
        
        # 一時ディレクトリの作成
        self.temp_dir = Path(tempfile.mkdtemp(prefix="techbridge_config_test_"))
        test_config_dir = self.temp_dir / "config"
        test_config_dir.mkdir(parents=True)
        
        # テスト用設定ファイルの作成
        self._create_test_configs(test_config_dir)
        
        print(f"📁 テスト環境: {self.temp_dir}")
        return self.temp_dir
    
    def _create_test_configs(self, config_dir: Path):
        """テスト用設定ファイルの作成"""
        
        # テーマ設定（正常データ）
        theme_config = {
            "version": "1.0",
            "default_theme": "light",
            "themes": {
                "light": {
                    "colors": {
                        "background": "#ffffff",
                        "foreground": "#000000",
                        "primary": "#0078d4",
                        "accent": "#28a745"
                    },
                    "styles": {
                        "button": "border-radius: 4px; padding: 8px 16px;"
                    }
                }
            }
        }
        
        # UI設定（正常データ）
        ui_config = {
            "version": "1.0",
            "layout": {
                "main_splitter": {
                    "table_ratio": 70,
                    "detail_ratio": 30
                }
            },
            "dimensions": {
                "border": {
                    "width": "1px",
                    "radius": {
                        "small": "2px",
                        "medium": "4px", 
                        "large": "8px"
                    }
                },
                "padding": {
                    "table_cell": "5px",
                    "header": "10px",
                    "button": "8px 16px"
                }
            }
        }
        
        # サーバー設定（正常データ）
        server_config = {
            "version": "1.0",
            "socket_server": {
                "port": 8888,
                "host": "localhost",
                "max_connections": 100,
                "timeouts": {
                    "connection": 30.0,
                    "read": 10.0,
                    "write": 10.0
                }
            },
            "http_server": {
                "port": 8080,
                "host": "localhost"
            }
        }
        
        # パス設定（正常データ）
        paths_config = {
            "version": "1.0",
            "base_paths": {
                "dev_root": "/mnt/c/Users/tky99/dev",
                "project_root": "/mnt/c/Users/tky99/dev/techbridge"
            },
            "dynamic_paths": {
                "output": {
                    "pdf_file": "/output/{n_number}.pdf"
                }
            },
            "security": {
                "forbidden_patterns": ["..", "/", "\\"],
                "allowed_patterns": ["*.pdf", "*.txt"]
            }
        }
        
        # 設定ファイル作成
        configs = {
            "theme_config.yaml": theme_config,
            "ui_config.yaml": ui_config,
            "server_config.yaml": server_config,
            "paths_config.yaml": paths_config
        }
        
        for filename, config_data in configs.items():
            config_path = config_dir / filename
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"テスト設定ファイル作成完了: {config_dir}")
    
    def _create_invalid_test_configs(self, config_dir: Path):
        """無効なテスト用設定ファイルの作成"""
        
        # 無効なテーマ設定（スキーマ違反）
        invalid_theme = {
            "version": "invalid_version",  # パターン違反
            "default_theme": "invalid_theme",  # enum違反
            "themes": {
                "light": {
                    "colors": {
                        "background": "invalid_color",  # 16進色違反
                        "foreground": "#000000"
                    }
                }
            }
        }
        
        # 無効なUI設定（カスタム検証違反）
        invalid_ui = {
            "version": "1.0",
            "layout": {
                "main_splitter": {
                    "table_ratio": 60,  # 合計が100にならない
                    "detail_ratio": 30
                }
            },
            "dimensions": {
                "border": {"width": "1px"},
                "padding": {"table_cell": "5px"}
            }
        }
        
        # 無効なサーバー設定（ポート重複）
        invalid_server = {
            "version": "1.0",
            "socket_server": {
                "port": 8888,
                "host": "localhost"
            },
            "http_server": {
                "port": 8888  # 同じポート番号
            }
        }
        
        configs = {
            "invalid_theme_config.yaml": invalid_theme,
            "invalid_ui_config.yaml": invalid_ui,
            "invalid_server_config.yaml": invalid_server
        }
        
        for filename, config_data in configs.items():
            config_path = config_dir / filename
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    def test_system_availability(self) -> TestResult:
        """システム利用可能性テスト"""
        try:
            if not NEW_CONFIG_SYSTEM_AVAILABLE:
                return TestResult(
                    "system_availability",
                    False,
                    "新しい設定システムが利用できません"
                )
            
            # 基本クラスのインポートテスト
            manager = EnhancedConfigManager(str(self.temp_dir))
            validator = ConfigValidator(str(self.temp_dir))
            
            return TestResult(
                "system_availability", 
                True,
                "設定システム利用可能",
                {"manager": str(type(manager)), "validator": str(type(validator))}
            )
            
        except Exception as e:
            return TestResult("system_availability", False, f"システム利用不可: {e}")
    
    def test_basic_config_loading(self) -> TestResult:
        """基本設定読み込みテスト"""
        try:
            with create_config_system(str(self.temp_dir)) as config:
                # 基本設定値の取得テスト
                theme = config.get('theme.default_theme', 'unknown')
                port = config.get('server.socket_server.port', 0)
                
                success = theme == 'light' and port == 8888
                
                return TestResult(
                    "basic_config_loading",
                    success,
                    f"設定読み込み{'成功' if success else '失敗'}",
                    {"theme": theme, "port": port}
                )
                
        except Exception as e:
            return TestResult("basic_config_loading", False, f"読み込み失敗: {e}")
    
    def test_environment_override(self) -> TestResult:
        """環境変数オーバーライドテスト"""
        try:
            # 環境変数設定
            test_port = 9999
            os.environ['TECHWF_TEST_PORT'] = str(test_port)
            
            with create_config_system(str(self.temp_dir)) as config:
                # 環境変数オーバーライドの取得
                port = config.get_with_env_override(
                    'server.socket_server.port',
                    'TECHWF_TEST_PORT', 
                    8888
                )
                
                success = int(port) == test_port  # 環境変数を整数に変換して比較
                
                # 環境変数クリーンアップ
                del os.environ['TECHWF_TEST_PORT']
                
                return TestResult(
                    "environment_override",
                    success,
                    f"環境変数オーバーライド{'成功' if success else '失敗'}",
                    {"expected": test_port, "actual": port}
                )
                
        except Exception as e:
            return TestResult("environment_override", False, f"オーバーライド失敗: {e}")
    
    def test_validation_system(self) -> TestResult:
        """設定検証システムテスト"""
        try:
            # 無効な設定ファイルを作成
            config_dir = self.temp_dir / "config"
            self._create_invalid_test_configs(config_dir)
            
            with create_config_system(str(self.temp_dir)) as config:
                validator = config.validator
                
                # 無効なテーマ設定を検証
                invalid_theme = yaml.safe_load(open(config_dir / "invalid_theme_config.yaml"))
                theme_result = validator.validate_config('theme', invalid_theme)
                
                # 無効なUI設定を検証
                invalid_ui = yaml.safe_load(open(config_dir / "invalid_ui_config.yaml"))
                ui_result = validator.validate_config('ui', invalid_ui)
                
                # 無効なサーバー設定を検証  
                invalid_server = yaml.safe_load(open(config_dir / "invalid_server_config.yaml"))
                server_result = validator.validate_config('server', invalid_server)
                
                # 全て無効な設定として検出されるはず
                success = (
                    not theme_result.is_valid and
                    not ui_result.is_valid and  
                    not server_result.is_valid
                )
                
                total_errors = (
                    len(theme_result.errors) +
                    len(ui_result.errors) + 
                    len(server_result.errors)
                )
                
                return TestResult(
                    "validation_system",
                    success,
                    f"検証システム{'正常' if success else '異常'}",
                    {
                        "theme_valid": theme_result.is_valid,
                        "ui_valid": ui_result.is_valid,
                        "server_valid": server_result.is_valid,
                        "total_errors": total_errors
                    }
                )
                
        except Exception as e:
            return TestResult("validation_system", False, f"検証テスト失敗: {e}")
    
    def test_fallback_system(self) -> TestResult:
        """フォールバックシステムテスト"""
        try:
            with create_config_system(str(self.temp_dir)) as config:
                validator = config.validator
                
                # 不完全な設定データ
                incomplete_theme = {
                    "version": "1.0",
                    "themes": {
                        "light": {
                            "colors": {}  # 必須カラーが不足
                        }
                    }
                }
                
                # フォールバック適用
                repaired_theme = validator.apply_fallbacks('theme', incomplete_theme)
                
                # フォールバック値が適用されているかチェック
                bg_color = repaired_theme.get('themes', {}).get('light', {}).get('colors', {}).get('background')
                fg_color = repaired_theme.get('themes', {}).get('light', {}).get('colors', {}).get('foreground')
                default_theme = repaired_theme.get('default_theme')
                
                success = (
                    bg_color == '#ffffff' and
                    fg_color == '#000000' and
                    default_theme == 'light'
                )
                
                return TestResult(
                    "fallback_system",
                    success,
                    f"フォールバック{'成功' if success else '失敗'}",
                    {
                        "background": bg_color,
                        "foreground": fg_color,
                        "default_theme": default_theme
                    }
                )
                
        except Exception as e:
            return TestResult("fallback_system", False, f"フォールバック失敗: {e}")
    
    def test_file_monitoring(self) -> TestResult:
        """ファイル監視テスト"""
        try:
            change_detected = False
            
            def on_change(change):
                nonlocal change_detected
                change_detected = True
                logger.info(f"設定変更検出: {change.config_name}")
            
            with create_config_system(str(self.temp_dir)) as config:
                # 変更コールバック登録
                config.watcher.add_change_callback(on_change)
                
                # 設定ファイル修正
                config_path = self.temp_dir / "config" / "theme_config.yaml"
                theme_data = yaml.safe_load(open(config_path))
                theme_data['default_theme'] = 'dark'
                
                with open(config_path, 'w') as f:
                    yaml.dump(theme_data, f)
                
                # 変更検出まで待機
                time.sleep(2)
                
                return TestResult(
                    "file_monitoring",
                    change_detected,
                    f"ファイル監視{'正常' if change_detected else '異常'}",
                    {"change_detected": change_detected}
                )
                
        except Exception as e:
            return TestResult("file_monitoring", False, f"監視テスト失敗: {e}")
    
    def test_system_integration(self) -> TestResult:
        """システム統合テスト"""
        try:
            with create_config_system(str(self.temp_dir), enable_auto_repair=True) as config:
                # 健全性状態の確認
                health = config.get_health_status()
                
                # システム状態レポートの生成
                report_path = config.export_system_report()
                report_exists = Path(report_path).exists()
                
                # 設定値アクセステスト
                theme = config.get('theme.default_theme')
                port = config.get('server.socket_server.port')
                path = config.get_path('paths.dynamic_paths.output.pdf_file', n_number='N12345')
                
                success = (
                    health['is_healthy'] and
                    report_exists and
                    theme is not None and
                    port is not None and
                    'N12345' in path
                )
                
                return TestResult(
                    "system_integration",
                    success,
                    f"統合テスト{'成功' if success else '失敗'}",
                    {
                        "health": health['is_healthy'],
                        "report_created": report_exists,
                        "theme": theme,
                        "port": port,
                        "formatted_path": path
                    }
                )
                
        except Exception as e:
            return TestResult("system_integration", False, f"統合テスト失敗: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """全テストの実行"""
        print("🧪 TechBridge設定システム総合テスト開始")
        print("=" * 60)
        
        # テスト環境構築
        self.setup_test_environment()
        
        # テスト実行
        tests = [
            ("システム利用可能性", self.test_system_availability),
            ("基本設定読み込み", self.test_basic_config_loading), 
            ("環境変数オーバーライド", self.test_environment_override),
            ("設定検証システム", self.test_validation_system),
            ("フォールバックシステム", self.test_fallback_system),
            ("ファイル監視", self.test_file_monitoring),
            ("システム統合", self.test_system_integration)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}テスト実行中...")
            try:
                result = test_func()
                self.test_results.append(result)
                
                status = "✅ 成功" if result.success else "❌ 失敗"
                print(f"{status}: {result.message}")
                
                if result.details:
                    for key, value in result.details.items():
                        print(f"   {key}: {value}")
                        
            except Exception as e:
                error_result = TestResult(test_name.lower().replace(' ', '_'), False, f"テスト例外: {e}")
                self.test_results.append(error_result)
                print(f"❌ 例外: {e}")
        
        # 結果集計
        return self._generate_test_report()
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """テスト結果レポート生成"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        print(f"実行テスト: {total_tests}")
        print(f"成功: {passed_tests} ✅")
        print(f"失敗: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失敗したテスト:")
            for result in self.test_results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.message}")
        
        # レポートデータ
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests/total_tests*100,
                "overall_status": "PASS" if failed_tests == 0 else "FAIL"
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "details": r.details or {}
                }
                for r in self.test_results
            ]
        }
        
        # レポートファイル出力
        if self.temp_dir:
            report_file = self.temp_dir / "test_report.yaml"
            with open(report_file, 'w', encoding='utf-8') as f:
                yaml.dump(report, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"\n📄 詳細レポート: {report_file}")
        
        return report
    
    def cleanup(self):
        """テスト環境クリーンアップ"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 テスト環境クリーンアップ: {self.temp_dir}")


def main():
    """メイン関数"""
    project_root = "/mnt/c/Users/tky99/dev/techbridge"
    
    tester = ConfigSystemTester(project_root)
    
    try:
        # 全テスト実行
        report = tester.run_all_tests()
        
        # Phase 5完了判定
        overall_success = report["test_summary"]["overall_status"] == "PASS"
        
        print("\n" + "=" * 60)
        if overall_success:
            print("🎉 Phase 5: 設定値検証とフォールバック機構の実装 - 完了")
            print("TechBridge設定システム全体が正常に動作しています！")
        else:
            print("⚠️  Phase 5: 一部のテストで問題が発見されました")
            print("設定システムの修正が必要です")
        print("=" * 60)
        
        return 0 if overall_success else 1
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return 1
        
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())