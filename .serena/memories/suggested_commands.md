# TechBridge Suggested Commands

## Development Commands

### Environment Setup
```bash
# Install dependencies with Poetry
make install
# or
poetry install

# Setup development environment  
make dev
```

### Running the Application
```bash
# Start development server
make run
# or
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with development script
./scripts/start_dev.sh
```

### Testing
```bash
# Run tests
make test
# or
poetry run pytest -v

# Run tests with coverage
make test-cov
# or  
poetry run pytest -v --cov=app --cov-report=html --cov-report=term
```

### Code Quality
```bash
# Check code quality (lint)
make lint
# Includes: black --check, isort --check-only, flake8, mypy

# Format code
make format  
# Includes: black, isort

# Clean temporary files
make clean
```

### Database Operations
```bash
# Run database migrations
make migrate
# or
poetry run alembic upgrade head

# Create new migration
make migrate-create
# or
poetry run alembic revision --autogenerate -m "migration_name"

# Rollback migration
make migrate-down
# or
poetry run alembic downgrade -1
```

### Docker Operations
```bash
# Build Docker image
make docker-build

# Start Docker containers
make docker-up

# Stop Docker containers  
make docker-down

# View Docker logs
make docker-logs

# Show running containers
make docker-ps
```

### Development Utilities
```bash
# Start Python shell
make shell
# or
poetry run python

# Database shell
make db-shell
# Access PostgreSQL directly

# Redis CLI
make redis-cli
# Access Redis directly
```

### Production Commands
```bash
# Build production image
make prod-build

# Run production container
make prod-run
```

## System Utilities (Linux)
- `ls` - List directory contents
- `cd` - Change directory  
- `pwd` - Print working directory
- `grep` - Search text patterns
- `find` - Find files and directories
- `git` - Version control operations
- `cat` - Display file contents
- `less` - View file contents with pagination
- `tail` - Display end of files
- `ps` - List running processes
- `top` - Display running processes dynamically

## Quick Reference
- **Main entry point**: `app/main.py`
- **Configuration**: `app/core/config.py`
- **Database models**: `app/models/`
- **API routes**: `app/api/`
- **Tests**: `tests/`
- **Environment variables**: `.env` (copy from `.env.example`)