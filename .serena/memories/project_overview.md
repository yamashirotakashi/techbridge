# TechBridge Project Overview

## Project Purpose
TechBridge is a comprehensive workflow management system for the Technical Book Publishing process. It serves as an integration platform that connects various tools and systems used in technical book production and publication workflows.

## Key Functionality
- **Workflow Management**: Manages the complete publication workflow from book discovery to completion
- **Slack Integration**: Provides Slack bot functionality for team communication and status updates  
- **Google Sheets Integration**: Synchronizes with Google Sheets for project tracking
- **External Service Integration**: Connects with various external APIs and services
- **Progress Tracking**: Tracks publication stages from discovery through final completion
- **Mini-App Platform**: Includes Project Initializer and other mini-applications

## Tech Stack
- **Framework**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Cache**: Redis for session storage and caching
- **Authentication**: JWT-based API authentication
- **External Integrations**: Slack API, Google Sheets API
- **Development Tools**: Poetry for dependency management
- **Testing**: pytest with coverage reporting
- **Code Quality**: Black (formatting), isort (imports), flake8 (linting), mypy (typing)

## Project Structure
- `app/`: Main FastAPI application code
  - `api/`: API endpoints and routes
  - `core/`: Core configuration, database, auth, logging
  - `models/`: SQLAlchemy database models
  - `schemas/`: Pydantic request/response models
  - `services/`: Business logic services
  - `crud/`: Database operations
- `techwf/`: TechWF GUI application (separate Tkinter-based component)
- `tests/`: Test suite with unit and integration tests
- `scripts/`: Development and deployment scripts
- `alembic/`: Database migration files

## Key Models
- **WorkflowItem**: Core workflow entity tracking publication progress
- **ProgressStatus**: Enum defining workflow stages (DISCOVERED → PURCHASED → MANUSCRIPT_REQUESTED → MANUSCRIPT_RECEIVED → FIRST_PROOF → SECOND_PROOF → COMPLETED)

## Current Status
The project appears to be in active development with both a web API (FastAPI) and a desktop GUI component (TechWF). The system is designed to handle the complete technical book publication workflow with multiple integration points.