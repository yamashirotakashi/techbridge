#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge設定検証システム
Phase 4: 外部設定ファイル構造実装 - 設定値検証機能

YAML設定ファイルの構造検証、値範囲チェック、
フォールバック機構を提供
"""

import os
import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """設定検証エラー情報"""
    config_name: str
    field_path: str
    error_type: str  # missing, invalid_type, invalid_value, schema_violation
    expected: str
    actual: Any
    message: str
    severity: str  # critical, high, medium, low


@dataclass
class ValidationResult:
    """設定検証結果"""
    config_name: str
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    validated_at: datetime
    fallback_applied: List[str]  # フォールバックが適用された設定パス


class ConfigValidator:
    """
    TechBridge設定検証エンジン
    
    YAML設定ファイルの構造・型・値範囲を検証し、
    問題がある場合はフォールバック値を適用
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.schemas = self._load_validation_schemas()
        self.validation_results: Dict[str, ValidationResult] = {}
        
    def _load_validation_schemas(self) -> Dict[str, Dict[str, Any]]:
        """設定検証スキーマの定義"""
        return {
            'theme': {
                'type': 'object',
                'required': ['version', 'default_theme', 'themes'],
                'properties': {
                    'version': {'type': 'string', 'pattern': r'^\d+\.\d+$'},
                    'default_theme': {
                        'type': 'string', 
                        'enum': ['light', 'dark', 'system']
                    },
                    'themes': {
                        'type': 'object',
                        'required': ['light'],
                        'properties': {
                            'light': {'$ref': '#/definitions/theme_config'},
                            'dark': {'$ref': '#/definitions/theme_config'}
                        }
                    }
                },
                'definitions': {
                    'theme_config': {
                        'type': 'object',
                        'required': ['colors'],
                        'properties': {
                            'colors': {
                                'type': 'object',
                                'required': ['background', 'foreground'],
                                'properties': {
                                    'background': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'},
                                    'foreground': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'},
                                    'primary': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'},
                                    'accent': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'},
                                    'error': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'},
                                    'warning': {'type': 'string', 'pattern': r'^#[0-9a-fA-F]{6}$'}
                                }
                            },
                            'styles': {
                                'type': 'object',
                                'properties': {
                                    'button': {'type': 'string'},
                                    'table_cell': {'type': 'string'},
                                    'menu_item': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            },
            
            'ui': {
                'type': 'object',
                'required': ['version', 'layout', 'dimensions'],
                'properties': {
                    'version': {'type': 'string', 'pattern': r'^\d+\.\d+$'},
                    'layout': {
                        'type': 'object',
                        'required': ['main_splitter'],
                        'properties': {
                            'main_splitter': {
                                'type': 'object',
                                'required': ['table_ratio', 'detail_ratio'],
                                'properties': {
                                    'table_ratio': {'type': 'integer', 'minimum': 10, 'maximum': 90},
                                    'detail_ratio': {'type': 'integer', 'minimum': 10, 'maximum': 90}
                                }
                            }
                        }
                    },
                    'dimensions': {
                        'type': 'object',
                        'required': ['border', 'padding'],
                        'properties': {
                            'border': {
                                'type': 'object',
                                'properties': {
                                    'width': {'type': 'string', 'pattern': r'^\d+px$'},
                                    'radius': {
                                        'type': 'object',
                                        'properties': {
                                            'small': {'type': 'string', 'pattern': r'^\d+px$'},
                                            'medium': {'type': 'string', 'pattern': r'^\d+px$'},
                                            'large': {'type': 'string', 'pattern': r'^\d+px$'}
                                        }
                                    }
                                }
                            },
                            'padding': {
                                'type': 'object',
                                'properties': {
                                    'table_cell': {'type': 'string', 'pattern': r'^\d+px$'},
                                    'header': {'type': 'string', 'pattern': r'^\d+px$'},
                                    'button': {'type': 'string', 'pattern': r'^\d+px( \d+px)?$'}
                                }
                            }
                        }
                    }
                }
            },
            
            'server': {
                'type': 'object',
                'required': ['version', 'socket_server'],
                'properties': {
                    'version': {'type': 'string', 'pattern': r'^\d+\.\d+$'},
                    'socket_server': {
                        'type': 'object',
                        'required': ['port'],
                        'properties': {
                            'port': {'type': 'integer', 'minimum': 1024, 'maximum': 65535},
                            'host': {'type': 'string'},
                            'max_connections': {'type': 'integer', 'minimum': 1, 'maximum': 1000},
                            'timeouts': {
                                'type': 'object',
                                'properties': {
                                    'connection': {'type': 'number', 'minimum': 1.0, 'maximum': 300.0},
                                    'read': {'type': 'number', 'minimum': 1.0, 'maximum': 60.0},
                                    'write': {'type': 'number', 'minimum': 1.0, 'maximum': 60.0}
                                }
                            }
                        }
                    },
                    'http_server': {
                        'type': 'object',
                        'properties': {
                            'port': {'type': 'integer', 'minimum': 1024, 'maximum': 65535},
                            'host': {'type': 'string'}
                        }
                    }
                }
            },
            
            'paths': {
                'type': 'object',
                'required': ['version', 'base_paths', 'security'],
                'properties': {
                    'version': {'type': 'string', 'pattern': r'^\d+\.\d+$'},
                    'base_paths': {
                        'type': 'object',
                        'required': ['dev_root', 'project_root'],
                        'properties': {
                            'dev_root': {'type': 'string'},
                            'project_root': {'type': 'string'}
                        }
                    },
                    'security': {
                        'type': 'object',
                        'required': ['forbidden_patterns'],
                        'properties': {
                            'forbidden_patterns': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'minItems': 1
                            },
                            'allowed_patterns': {
                                'type': 'array',
                                'items': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    
    def validate_config(self, config_name: str, config_data: Dict[str, Any]) -> ValidationResult:
        """
        設定データの検証
        
        Args:
            config_name: 設定名
            config_data: 設定データ
            
        Returns:
            検証結果
        """
        errors = []
        warnings = []
        fallback_applied = []
        
        try:
            # JSONスキーマ検証
            schema = self.schemas.get(config_name)
            if schema:
                jsonschema.validate(config_data, schema)
                logger.info(f"設定スキーマ検証成功: {config_name}")
            else:
                warnings.append(ValidationError(
                    config_name=config_name,
                    field_path="schema",
                    error_type="schema_missing",
                    expected="validation schema",
                    actual="none",
                    message=f"設定スキーマが定義されていません: {config_name}",
                    severity="medium"
                ))
            
            # カスタム検証ルール
            custom_errors, custom_warnings, custom_fallbacks = self._custom_validation(
                config_name, config_data
            )
            errors.extend(custom_errors)
            warnings.extend(custom_warnings)
            fallback_applied.extend(custom_fallbacks)
            
        except jsonschema.ValidationError as e:
            errors.append(ValidationError(
                config_name=config_name,
                field_path='.'.join(str(x) for x in e.path) if e.path else "root",
                error_type="schema_violation",
                expected=str(e.schema),
                actual=e.instance,
                message=e.message,
                severity=self._determine_error_severity(e)
            ))
        except Exception as e:
            errors.append(ValidationError(
                config_name=config_name,
                field_path="unknown",
                error_type="validation_error",
                expected="valid configuration",
                actual=str(e),
                message=f"検証エラー: {e}",
                severity="critical"
            ))
        
        result = ValidationResult(
            config_name=config_name,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now(),
            fallback_applied=fallback_applied
        )
        
        self.validation_results[config_name] = result
        return result
    
    def _custom_validation(self, config_name: str, config_data: Dict[str, Any]) -> tuple:
        """カスタム検証ルール"""
        errors = []
        warnings = []
        fallback_applied = []
        
        if config_name == 'ui':
            # UI設定の特別チェック
            layout = config_data.get('layout', {}).get('main_splitter', {})
            table_ratio = layout.get('table_ratio', 0)
            detail_ratio = layout.get('detail_ratio', 0)
            
            if table_ratio + detail_ratio != 100:
                errors.append(ValidationError(
                    config_name=config_name,
                    field_path="layout.main_splitter",
                    error_type="invalid_value",
                    expected="sum equals 100",
                    actual=f"{table_ratio} + {detail_ratio} = {table_ratio + detail_ratio}",
                    message="テーブルと詳細の比率の合計は100である必要があります",
                    severity="high"
                ))
                
        elif config_name == 'server':
            # サーバー設定の特別チェック
            socket_port = config_data.get('socket_server', {}).get('port')
            http_port = config_data.get('http_server', {}).get('port')
            
            if socket_port and http_port and socket_port == http_port:
                errors.append(ValidationError(
                    config_name=config_name,
                    field_path="ports",
                    error_type="invalid_value",
                    expected="different ports",
                    actual=f"both using {socket_port}",
                    message="ソケットサーバーとHTTPサーバーで同じポートは使用できません",
                    severity="critical"
                ))
                
        elif config_name == 'paths':
            # パス設定のセキュリティチェック
            forbidden_patterns = config_data.get('security', {}).get('forbidden_patterns', [])
            if '..' not in forbidden_patterns:
                warnings.append(ValidationError(
                    config_name=config_name,
                    field_path="security.forbidden_patterns",
                    error_type="security_warning",
                    expected="contains '..'",
                    actual=str(forbidden_patterns),
                    message="パストラバーサル防止のため '..' を禁止パターンに追加することを推奨",
                    severity="medium"
                ))
        
        return errors, warnings, fallback_applied
    
    def _determine_error_severity(self, error: jsonschema.ValidationError) -> str:
        """エラー重要度の判定"""
        if 'required' in str(error.schema):
            return "critical"
        elif error.validator in ['type', 'enum']:
            return "high"
        elif error.validator in ['pattern', 'minimum', 'maximum']:
            return "medium"
        else:
            return "low"
    
    def apply_fallbacks(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        フォールバック値の適用
        
        Args:
            config_name: 設定名
            config_data: 元の設定データ
            
        Returns:
            フォールバック適用後の設定データ
        """
        fallback_data = config_data.copy()
        fallback_rules = self._get_fallback_rules(config_name)
        
        for rule in fallback_rules:
            current = fallback_data
            path_parts = rule['path'].split('.')
            
            # パス途中まで辿って、最後のキーで値を設定
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # 値が存在しないか無効な場合にフォールバック適用
            final_key = path_parts[-1]
            if final_key not in current or not self._is_valid_value(
                current[final_key], rule['validator']
            ):
                current[final_key] = rule['fallback']
                logger.info(f"フォールバック適用: {config_name}.{rule['path']} = {rule['fallback']}")
        
        return fallback_data
    
    def _get_fallback_rules(self, config_name: str) -> List[Dict[str, Any]]:
        """フォールバック規則の定義"""
        rules = {
            'theme': [
                {
                    'path': 'default_theme',
                    'validator': lambda x: x in ['light', 'dark', 'system'],
                    'fallback': 'light'
                },
                {
                    'path': 'themes.light.colors.background',
                    'validator': lambda x: isinstance(x, str) and x.startswith('#'),
                    'fallback': '#ffffff'
                },
                {
                    'path': 'themes.light.colors.foreground',
                    'validator': lambda x: isinstance(x, str) and x.startswith('#'),
                    'fallback': '#000000'
                }
            ],
            'ui': [
                {
                    'path': 'layout.main_splitter.table_ratio',
                    'validator': lambda x: isinstance(x, int) and 10 <= x <= 90,
                    'fallback': 70
                },
                {
                    'path': 'layout.main_splitter.detail_ratio',
                    'validator': lambda x: isinstance(x, int) and 10 <= x <= 90,
                    'fallback': 30
                },
                {
                    'path': 'dimensions.border.width',
                    'validator': lambda x: isinstance(x, str) and x.endswith('px'),
                    'fallback': '1px'
                }
            ],
            'server': [
                {
                    'path': 'socket_server.port',
                    'validator': lambda x: isinstance(x, int) and 1024 <= x <= 65535,
                    'fallback': 8888
                },
                {
                    'path': 'socket_server.host',
                    'validator': lambda x: isinstance(x, str) and x,
                    'fallback': 'localhost'
                },
                {
                    'path': 'socket_server.timeouts.connection',
                    'validator': lambda x: isinstance(x, (int, float)) and x > 0,
                    'fallback': 30.0
                }
            ],
            'paths': [
                {
                    'path': 'base_paths.dev_root',
                    'validator': lambda x: isinstance(x, str) and x,
                    'fallback': '/mnt/c/Users/tky99/dev'
                },
                {
                    'path': 'security.forbidden_patterns',
                    'validator': lambda x: isinstance(x, list) and len(x) > 0,
                    'fallback': ['..', '/', '\\']
                }
            ]
        }
        
        return rules.get(config_name, [])
    
    def _is_valid_value(self, value: Any, validator: callable) -> bool:
        """値の有効性チェック"""
        try:
            return validator(value)
        except:
            return False
    
    def export_validation_report(self, output_path: Optional[str] = None) -> str:
        """
        検証レポートの出力
        
        Args:
            output_path: 出力ファイルパス
            
        Returns:
            出力ファイルパス
        """
        if output_path is None:
            output_path = f"config_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        
        report_data = {
            'validation_summary': {
                'total_configs': len(self.validation_results),
                'valid_configs': sum(1 for r in self.validation_results.values() if r.is_valid),
                'invalid_configs': sum(1 for r in self.validation_results.values() if not r.is_valid),
                'total_errors': sum(len(r.errors) for r in self.validation_results.values()),
                'total_warnings': sum(len(r.warnings) for r in self.validation_results.values()),
                'generated_at': datetime.now().isoformat()
            },
            'results': {
                name: asdict(result) for name, result in self.validation_results.items()
            }
        }
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(report_data, file, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"設定検証レポート出力完了: {output_file}")
        return str(output_file)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """検証結果サマリーの取得"""
        critical_errors = []
        high_errors = []
        all_warnings = []
        
        for result in self.validation_results.values():
            for error in result.errors:
                if error.severity == 'critical':
                    critical_errors.append(error)
                elif error.severity == 'high':
                    high_errors.append(error)
            
            all_warnings.extend(result.warnings)
        
        return {
            'total_configs': len(self.validation_results),
            'valid_configs': sum(1 for r in self.validation_results.values() if r.is_valid),
            'critical_errors': len(critical_errors),
            'high_errors': len(high_errors),
            'total_warnings': len(all_warnings),
            'overall_status': 'valid' if len(critical_errors) == 0 else 'invalid',
            'critical_issues': [
                {
                    'config': error.config_name,
                    'path': error.field_path,
                    'message': error.message
                }
                for error in critical_errors[:5]  # 最初の5件
            ]
        }


if __name__ == "__main__":
    # 設定検証システムのテスト
    validator = ConfigValidator("/mnt/c/Users/tky99/dev/techbridge")
    
    print("=== TechBridge設定検証システム テスト ===")
    
    # 設定ファイルの検証テスト
    test_configs = {
        'theme': {
            'version': '1.0',
            'default_theme': 'light',
            'themes': {
                'light': {
                    'colors': {
                        'background': '#ffffff',
                        'foreground': '#000000'
                    }
                }
            }
        },
        'ui': {
            'version': '1.0',
            'layout': {
                'main_splitter': {
                    'table_ratio': 70,
                    'detail_ratio': 30
                }
            },
            'dimensions': {
                'border': {'width': '1px'},
                'padding': {'table_cell': '5px'}
            }
        }
    }
    
    for config_name, config_data in test_configs.items():
        result = validator.validate_config(config_name, config_data)
        print(f"設定 {config_name}: {'有効' if result.is_valid else '無効'}")
        if result.errors:
            for error in result.errors[:3]:  # 最初の3件
                print(f"  エラー: {error.message}")
        if result.warnings:
            for warning in result.warnings[:2]:  # 最初の2件
                print(f"  警告: {warning.message}")
    
    # 検証サマリー表示
    summary = validator.get_validation_summary()
    print(f"\n検証サマリー:")
    print(f"- 合計設定: {summary['total_configs']}")
    print(f"- 有効設定: {summary['valid_configs']}")
    print(f"- 重大エラー: {summary['critical_errors']}")
    print(f"- 警告: {summary['total_warnings']}")
    
    print("=== テスト完了 ===")