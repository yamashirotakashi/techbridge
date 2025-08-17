# main.py インポート文修正が必要

## 現在の問題
1. 126-127行: except ImportError:ブロック内に間違ってimport文が配置
2. 129-132行: get_config_path関数にreturn文が複数回重複
3. 104行: 正しい位置にWorkerThreadインポート文は既に存在

## 正しい構造
```python
try:
    from path_resolver import get_config_path
except ImportError:
    def get_config_path(filename):
        return f"config/{filename}"
```

## 必要な修正
1. 127行の間違った位置のimport文を削除
2. get_config_path関数の重複return文を修正
3. 正しいインデントに修正

## 実装状況
- ✅ WorkerThreadクラスをcore/worker_thread.pyに分離完了
- ✅ 104行にWorkerThreadインポート文配置完了
- ❌ 構文エラー修正が必要（127行の不正import文）