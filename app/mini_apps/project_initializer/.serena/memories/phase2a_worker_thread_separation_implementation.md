# PJINIT v2.0 Phase 2A WorkerThread分離実装

## 実装対象
- **ファイル**: main.py 129-401行（274行）のWorkerThreadクラス
- **移動先**: core/worker_thread.py（新規作成）
- **クラス**: QThreadを継承した独立ワーカークラス

## WorkerThreadクラス分析結果

### 主要機能
1. **非同期処理用のワーカースレッド**
   - QThreadを継承
   - PyQtシグナル（progress, finished, error）を使用
   - タスクタイプに応じた処理分岐

2. **サポートタスク**
   - `initialize_project`: プロジェクト初期化
   - `check_project`: プロジェクト情報確認

3. **依存関係**
   - Google Sheets クライアント
   - Slack クライアント  
   - GitHub クライアント
   - PyQtシグナル（PyQt6）
   - asyncio（非同期処理）

### インポート依存関係
```python
# 必要なインポート
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
from typing import Dict, Any
import os

# クライアント依存関係
from clients.google_sheets_client import GoogleSheetsClient
from clients.slack_client import SlackClient  
from clients.github_client import GitHubClient

# 設定・ユーティリティ
from config.config_manager import get_config_path
from utils.availability_checker import (
    google_sheets_available,
    slack_client_available, 
    github_client_available
)
```

## 実装計画

### Step 1: core/worker_thread.py作成
- 適切なインポート文を配置
- WorkerThreadクラスを移動

### Step 2: main.py更新
- WorkerThreadクラス削除（129-401行）
- インポート文追加: `from core.worker_thread import WorkerThread`

### Step 3: 整合性確認
- 既存動作の完全保持
- 全機能テスト

## 制約条件遵守
- GUI/ワークフロー/外部連携への影響ゼロ
- 既存動作100%保持
- Serena MCPツールのみ使用