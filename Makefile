.PHONY: help install dev test lint format clean run docker-build docker-up docker-down migrate

# デフォルトターゲット
.DEFAULT_GOAL := help

# ヘルプ
help: ## ヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 依存関係のインストール
install: ## 依存関係をインストール
	poetry install

# 開発環境のセットアップ
dev: install ## 開発環境をセットアップ
	cp .env.example .env
	@echo "開発環境のセットアップが完了しました。.envファイルを編集してください。"

# テストの実行
test: ## テストを実行
	poetry run pytest -v

test-cov: ## カバレッジ付きでテストを実行
	poetry run pytest -v --cov=app --cov-report=html --cov-report=term

# リント
lint: ## コードをチェック
	poetry run black --check app tests
	poetry run isort --check-only app tests
	poetry run flake8 app tests
	poetry run mypy app

# フォーマット
format: ## コードをフォーマット
	poetry run black app tests
	poetry run isort app tests

# クリーンアップ
clean: ## 一時ファイルを削除
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# アプリケーションの実行
run: ## 開発サーバーを起動
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker関連
docker-build: ## Dockerイメージをビルド
	docker-compose build

docker-up: ## Dockerコンテナを起動
	docker-compose up -d

docker-down: ## Dockerコンテナを停止
	docker-compose down

docker-logs: ## Dockerログを表示
	docker-compose logs -f

docker-ps: ## 実行中のコンテナを表示
	docker-compose ps

# データベース関連
migrate: ## データベースマイグレーションを実行
	poetry run alembic upgrade head

migrate-create: ## 新しいマイグレーションを作成
	@read -p "マイグレーション名を入力してください: " name; \
	poetry run alembic revision --autogenerate -m "$$name"

migrate-down: ## マイグレーションをロールバック
	poetry run alembic downgrade -1

# 開発用コマンド
shell: ## Pythonシェルを起動
	poetry run python

db-shell: ## データベースシェルを起動
	docker-compose exec postgres psql -U techbridge -d techbridge

redis-cli: ## Redisクライアントを起動
	docker-compose exec redis redis-cli

# プロダクション用
prod-build: ## プロダクション用イメージをビルド
	docker build -t ghcr.io/yamashirotakashi/techbridge:latest .

prod-run: ## プロダクション用コンテナを起動
	docker run -d \
		--name techbridge \
		-p 8000:8000 \
		--env-file .env \
		ghcr.io/yamashirotakashi/techbridge:latest