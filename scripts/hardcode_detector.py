#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechBridge ハードコード検出・置換自動化ツール
Phase 3: 自動化ツール作成

外部設定化が必要なハードコード値を自動検出し、
設定ファイルへの置換を支援する
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class HardcodePattern:
    """ハードコードパターン定義"""
    name: str
    pattern: str
    category: str
    priority: str  # critical, high, medium, low
    description: str
    replacement_template: str


@dataclass
class HardcodeMatch:
    """ハードコード検出結果"""
    file_path: str
    line_number: int
    line_content: str
    match_value: str
    pattern_name: str
    category: str
    priority: str
    suggested_replacement: str


class HardcodeDetector:
    """ハードコード検出エンジン"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.patterns = self._load_detection_patterns()
        self.matches: List[HardcodeMatch] = []
        
    def _load_detection_patterns(self) -> List[HardcodePattern]:
        """検出パターンの定義を読み込み"""
        return [
            # カラーコード検出
            HardcodePattern(
                name="hex_colors",
                pattern=r'#[0-9a-fA-F]{3,6}',
                category="colors",
                priority="high",
                description="16進数カラーコード",
                replacement_template="config.get('theme.themes.{theme}.colors.{color_name}')"
            ),
            
            # CSS寸法値検出
            HardcodePattern(
                name="css_dimensions",
                pattern=r'\d+px|\d+em|\d+rem|\d+%',
                category="dimensions",
                priority="high", 
                description="CSS寸法値",
                replacement_template="config.get('ui.dimensions.{dimension_type}.{dimension_name}')"
            ),
            
            # 絶対ファイルパス検出
            HardcodePattern(
                name="absolute_paths",
                pattern=r'["\'](?:/[^"\']*|[A-Z]:[^"\']*)["\']',
                category="paths",
                priority="critical",
                description="絶対ファイルパス",
                replacement_template="config.get_path('paths.{path_category}.{path_name}')"
            ),
            
            # ポート番号検出
            HardcodePattern(
                name="port_numbers",
                pattern=r'port\s*[=:]\s*\d+',
                category="network",
                priority="critical",
                description="ポート番号",
                replacement_template="config.get_with_env_override('server.{service}.port', '{env_var}', {default})"
            ),
            
            # タイムアウト値検出
            HardcodePattern(
                name="timeout_values",
                pattern=r'timeout\s*[=:]\s*\d+\.?\d*',
                category="network",
                priority="high",
                description="タイムアウト値",
                replacement_template="config.get('server.{service}.timeouts.{timeout_type}')"
            ),
            
            # マジックナンバー検出（統計初期値等）
            HardcodePattern(
                name="magic_numbers",
                pattern=r'["\'](?:processed|failed|filtered)["\']\s*:\s*\d+',
                category="constants",
                priority="medium",
                description="統計初期値等のマジックナンバー",
                replacement_template="config.get('server.event_processing.initial_stats.{stat_name}')"
            ),
            
            # 設定ファイル名検出
            HardcodePattern(
                name="config_filenames",
                pattern=r'["\'][^"\']*\.(?:json|yaml|yml|ini|cfg|conf)["\']',
                category="config",
                priority="medium",
                description="設定ファイル名",
                replacement_template="config.get('paths.config_files.{config_type}')"
            ),
        ]
    
    def detect_hardcodes(self, file_patterns: List[str] = None) -> List[HardcodeMatch]:
        """
        ハードコード値の検出
        
        Args:
            file_patterns: 検査対象ファイルパターン
            
        Returns:
            検出されたハードコード一覧
        """
        if file_patterns is None:
            file_patterns = ["**/*.py"]
            
        self.matches = []
        
        for pattern in file_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    self._scan_file(file_path)
                    
        logger.info(f"ハードコード検出完了: {len(self.matches)}件")
        return self.matches
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """ファイルをスキップするかの判定"""
        skip_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            'venv', '.venv', 'venv_exe', 'venv_windows', 'env',
            'dist', 'build', '.tox', 'backup', 'archive',
            'site-packages', 'lib', 'Scripts', 'bin', 'include'
        }
        skip_files = {
            'config_manager.py',  # 設定管理ファイル自体は除外
            'hardcode_detector.py'  # 自分自身も除外
        }
        
        # ディレクトリチェック
        for part in file_path.parts:
            if part in skip_dirs:
                return True
                
        # ファイル名チェック
        if file_path.name in skip_files:
            return True
            
        # 特定のパスパターンをスキップ
        path_str = str(file_path)
        skip_patterns = [
            'site-packages',
            'venv',
            'node_modules',
            'dist/',
            'build/',
            '.git/',
            '__pycache__'
        ]
        
        for pattern in skip_patterns:
            if pattern in path_str:
                return True
        
        return False
    
    def _scan_file(self, file_path: Path):
        """単一ファイルの検査"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern in self.patterns:
                    matches = re.finditer(pattern.pattern, line)
                    for match in matches:
                        # 除外すべきマッチの判定
                        if self._should_skip_match(line, match, pattern):
                            continue
                            
                        hardcode_match = HardcodeMatch(
                            file_path=str(file_path),
                            line_number=line_num,
                            line_content=line.strip(),
                            match_value=match.group(),
                            pattern_name=pattern.name,
                            category=pattern.category,
                            priority=pattern.priority,
                            suggested_replacement=self._generate_replacement(match, pattern, line)
                        )
                        self.matches.append(hardcode_match)
                        
        except Exception as e:
            logger.error(f"ファイル読み込みエラー {file_path}: {e}")
    
    def _should_skip_match(self, line: str, match: re.Match, pattern: HardcodePattern) -> bool:
        """マッチをスキップするかの判定"""
        # コメント行はスキップ
        if line.strip().startswith('#'):
            return True
            
        # ドキュメントストリング内はスキップ
        if '"""' in line or "'''" in line:
            return True
            
        # パターン別除外ルール
        if pattern.name == "absolute_paths":
            # 相対パスや変数使用はスキップ
            if not (match.group().startswith('"/') or match.group().startswith("'/")):
                return True
                
        elif pattern.name == "css_dimensions":
            # "0px" のような値はスキップ
            if match.group().startswith('0'):
                return True
                
        return False
    
    def _generate_replacement(self, match: re.Match, pattern: HardcodePattern, line: str) -> str:
        """置換候補の生成"""
        value = match.group()
        
        if pattern.name == "hex_colors":
            # カラーコードから色名を推測
            color_map = {
                '#ffffff': 'background', '#000000': 'foreground',
                '#0078d4': 'primary', '#28a745': 'accent',
                '#dc3545': 'error', '#ffc107': 'warning'
            }
            color_name = color_map.get(value.lower(), 'custom_color')
            return f"config.get('theme.themes.{{theme}}.colors.{color_name}', '{value}')"
            
        elif pattern.name == "port_numbers":
            if '8888' in value:
                return "config.get_with_env_override('server.socket_server.port', 'TECHWF_SOCKET_PORT', 8888)"
            elif '8000' in value:
                return "config.get_with_env_override('server.http_server.port', 'TECHWF_HTTP_PORT', 8000)"
                
        elif pattern.name == "config_filenames":
            filename = value.strip('"\'')
            if filename == "ui_state.json":
                return "config.get('paths.config_files.ui_state')"
            elif filename == "config.json":
                return "config.get('paths.config_files.app_config')"
                
        # デフォルト置換案
        return pattern.replacement_template.format(
            value=value, 
            category=pattern.category,
            name=pattern.name
        )
    
    def export_report(self, output_path: str = None) -> str:
        """検出結果レポートの出力"""
        if output_path is None:
            output_path = f"hardcode_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            
        report_data = {
            'detection_summary': {
                'total_matches': len(self.matches),
                'by_category': self._group_by_category(),
                'by_priority': self._group_by_priority(),
                'detected_at': datetime.now().isoformat()
            },
            'matches': [asdict(match) for match in self.matches]
        }
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as file:
            yaml.dump(report_data, file, default_flow_style=False, allow_unicode=True, indent=2)
            
        logger.info(f"検出レポート出力完了: {output_file}")
        return str(output_file)
    
    def _group_by_category(self) -> Dict[str, int]:
        """カテゴリ別集計"""
        categories = {}
        for match in self.matches:
            categories[match.category] = categories.get(match.category, 0) + 1
        return categories
    
    def _group_by_priority(self) -> Dict[str, int]:
        """優先度別集計"""
        priorities = {}
        for match in self.matches:
            priorities[match.priority] = priorities.get(match.priority, 0) + 1
        return priorities


class HardcodeReplacer:
    """ハードコード置換エンジン"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup" / f"hardcode_replacement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def apply_replacements(self, matches: List[HardcodeMatch], auto_apply: bool = False) -> Dict[str, int]:
        """
        ハードコード置換の実行
        
        Args:
            matches: 置換対象のマッチ一覧
            auto_apply: 自動適用モード
            
        Returns:
            置換結果統計
        """
        stats = {'replaced': 0, 'skipped': 0, 'failed': 0}
        
        # ファイル別にグループ化
        file_matches = {}
        for match in matches:
            if match.file_path not in file_matches:
                file_matches[match.file_path] = []
            file_matches[match.file_path].append(match)
        
        for file_path, file_matches_list in file_matches.items():
            try:
                result = self._replace_in_file(file_path, file_matches_list, auto_apply)
                stats['replaced'] += result['replaced']
                stats['skipped'] += result['skipped']
                stats['failed'] += result['failed']
            except Exception as e:
                logger.error(f"ファイル置換エラー {file_path}: {e}")
                stats['failed'] += len(file_matches_list)
                
        logger.info(f"置換完了 - 成功: {stats['replaced']}, スキップ: {stats['skipped']}, 失敗: {stats['failed']}")
        return stats
    
    def _replace_in_file(self, file_path: str, matches: List[HardcodeMatch], auto_apply: bool) -> Dict[str, int]:
        """単一ファイルでの置換処理"""
        stats = {'replaced': 0, 'skipped': 0, 'failed': 0}
        file_obj = Path(file_path)
        
        # バックアップ作成
        backup_path = self.backup_dir / file_obj.name
        backup_path.write_text(file_obj.read_text(encoding='utf-8'), encoding='utf-8')
        
        try:
            with open(file_obj, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # 行番号の降順でソート（後ろから置換して行番号のずれを防ぐ）
            matches_sorted = sorted(matches, key=lambda m: m.line_number, reverse=True)
            
            for match in matches_sorted:
                line_idx = match.line_number - 1
                if line_idx < len(lines):
                    original_line = lines[line_idx]
                    
                    if auto_apply or self._confirm_replacement(match):
                        # 置換実行
                        new_line = original_line.replace(match.match_value, match.suggested_replacement)
                        lines[line_idx] = new_line
                        stats['replaced'] += 1
                        logger.info(f"置換完了 {file_path}:{match.line_number} {match.match_value} -> {match.suggested_replacement}")
                    else:
                        stats['skipped'] += 1
                else:
                    stats['failed'] += 1
            
            # ファイル書き込み
            with open(file_obj, 'w', encoding='utf-8') as file:
                file.writelines(lines)
                
        except Exception as e:
            # エラー時はバックアップから復元
            file_obj.write_text(backup_path.read_text(encoding='utf-8'), encoding='utf-8')
            raise e
            
        return stats
    
    def _confirm_replacement(self, match: HardcodeMatch) -> bool:
        """置換確認（インタラクティブモード用）"""
        print(f"\n置換候補:")
        print(f"ファイル: {match.file_path}:{match.line_number}")
        print(f"元の値: {match.match_value}")
        print(f"置換後: {match.suggested_replacement}")
        print(f"行内容: {match.line_content}")
        
        response = input("置換しますか？ (y/n/q): ").lower().strip()
        if response == 'q':
            exit(0)
        return response == 'y'


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TechBridge ハードコード検出・置換ツール")
    parser.add_argument("--project-root", default="/mnt/c/Users/tky99/dev/techbridge",
                       help="プロジェクトルートディレクトリ")
    parser.add_argument("--detect-only", action="store_true",
                       help="検出のみ実行（置換は行わない）")
    parser.add_argument("--auto-replace", action="store_true",
                       help="自動置換モード（確認なし）")
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"],
                       help="指定した優先度以上のみ処理")
    parser.add_argument("--category", help="指定したカテゴリのみ処理")
    parser.add_argument("--output", help="レポート出力ファイル名")
    
    args = parser.parse_args()
    
    print("=== TechBridge ハードコード検出・置換ツール ===")
    
    # 検出実行
    detector = HardcodeDetector(args.project_root)
    matches = detector.detect_hardcodes()
    
    # フィルタリング
    if args.priority:
        priority_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_priority = priority_levels[args.priority]
        matches = [m for m in matches if priority_levels.get(m.priority, 0) >= min_priority]
        
    if args.category:
        matches = [m for m in matches if m.category == args.category]
    
    print(f"検出されたハードコード: {len(matches)}件")
    
    # レポート出力
    report_path = detector.export_report(args.output)
    print(f"レポート出力: {report_path}")
    
    # 置換処理
    if not args.detect_only and matches:
        replacer = HardcodeReplacer(args.project_root)
        stats = replacer.apply_replacements(matches, args.auto_replace)
        print(f"置換結果: {stats}")


if __name__ == "__main__":
    main()