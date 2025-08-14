# TechBridge Coding Standards and Conventions

## Code Style Configuration

### Python Code Formatting
- **Black**: Code formatter with line length 88 characters
- **isort**: Import sorting with black profile compatibility
  - `multi_line_output = 3`
  - `include_trailing_comma = true`
  - `force_grid_wrap = 0`
  - `use_parentheses = true`
  - `ensure_newline_before_comments = true`
  - `line_length = 88`

### Type Checking
- **mypy**: Static type checker enabled
  - `python_version = "3.12"`
  - `warn_return_any = true`
  - `warn_unused_configs = true`
  - `disallow_untyped_defs = true`
  - `ignore_missing_imports = true`

### Linting
- **flake8**: PEP 8 compliance checking

## Naming Conventions

### Classes
- Use PascalCase: `WorkflowItem`, `ProgressStatus`
- Enum classes follow same convention: `NotificationChannel`

### Functions and Variables
- Use snake_case: `workflow_metadata`, `created_at`
- Private methods/attributes use leading underscore: `_internal_method`

### Constants
- Use UPPER_SNAKE_CASE: `API_V1_STR`, `ACCESS_TOKEN_EXPIRE_MINUTES`

### Database Fields
- Use snake_case for column names: `n_number`, `book_id`, `created_at`
- Use descriptive names: `workflow_metadata` instead of just `metadata`

## Type Hints

### Required Usage
- All function parameters and return types must have type hints
- Use `Optional[T]` for nullable fields
- Use `Mapped[T]` for SQLAlchemy model fields
- Use generic types where appropriate: `Dict[str, Any]`, `List[str]`

### Example Patterns
```python
# SQLAlchemy models
class WorkflowItem(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    workflow_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

# Service methods  
async def get_workflow_item(self, item_id: int) -> Optional[WorkflowItem]:
    return await self.session.get(WorkflowItem, item_id)
```

## Docstrings

### Class Docstrings
```python
class WorkflowItem(Base):
    """Workflow item model."""
```

### Method Docstrings
- Use simple descriptive strings for straightforward methods
- Include parameter and return type information for complex methods
- Use Japanese for user-facing display methods:
```python
@classmethod
def get_display_name(cls, status: 'ProgressStatus') -> str:
    """表示名を取得"""
```

## Project Structure Patterns

### Layer Separation
- **Models** (`app/models/`): Database entities and enums
- **Schemas** (`app/schemas/`): Pydantic request/response models  
- **Services** (`app/services/`): Business logic
- **CRUD** (`app/crud/`): Database operations
- **API** (`app/api/`): HTTP endpoints

### Import Organization
- Standard library imports first
- Third-party imports second
- Local application imports last
- Use absolute imports for project modules

### Configuration Management
- Use Pydantic Settings for configuration
- Environment variables with sensible defaults
- Separate development and production configs
- Validation for required settings

## Database Patterns

### Model Definition
- Use SQLAlchemy 2.0 style with `Mapped[T]`
- Include `created_at` and `updated_at` timestamps
- Use appropriate constraints and indexes
- Include `__repr__` methods for debugging

### Enum Integration
- Use Python Enums with SQLAlchemy enum columns
- Include display methods and emoji support for user interfaces
- Implement state transition logic where applicable

## Testing Standards

### Test Organization
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/` 
- Use pytest fixtures for common setup
- Async test support with `pytest-asyncio`

### Coverage Requirements
- Maintain high test coverage
- Use coverage reports to identify gaps
- Focus on business logic and critical paths

## Documentation

### Code Comments
- Use English for technical implementation comments
- Use Japanese for user-facing strings and display logic
- Explain complex business logic and state transitions
- Document API endpoint purposes and parameters