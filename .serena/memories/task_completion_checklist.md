# Task Completion Checklist

When completing a task in the TechBridge project, ensure the following steps are performed:

## Code Quality Checks
1. **Format Code**
   ```bash
   make format
   # or
   poetry run black app tests
   poetry run isort app tests
   ```

2. **Run Linting**  
   ```bash
   make lint
   # Includes: black --check, isort --check-only, flake8, mypy
   ```

3. **Type Checking**
   - Ensure all new code has proper type hints
   - Run `poetry run mypy app` and fix any type issues
   - Use `Optional[T]` for nullable fields
   - Use `Mapped[T]` for SQLAlchemy model fields

## Testing Requirements
1. **Run Full Test Suite**
   ```bash
   make test
   # or
   poetry run pytest -v
   ```

2. **Check Test Coverage**
   ```bash  
   make test-cov
   # Target: Maintain high coverage for business logic
   ```

3. **Write Tests for New Code**
   - Unit tests for business logic
   - Integration tests for API endpoints
   - Test both success and error cases

## Database Changes
1. **Create Migration if Needed**
   ```bash
   make migrate-create
   # Enter descriptive migration name
   ```

2. **Test Migration**
   ```bash
   make migrate
   # Ensure migration runs successfully
   ```

3. **Update Model Documentation**
   - Add docstrings to new models
   - Document any new enum values
   - Update field descriptions

## Documentation Updates
1. **Update Code Comments**
   - Add docstrings to new classes and methods
   - Explain complex business logic
   - Use Japanese for user-facing display methods

2. **Update API Documentation**
   - Ensure FastAPI auto-generates correct docs
   - Add example request/response bodies if needed
   - Document any new endpoints

## Final Verification
1. **Clean Build Test**
   ```bash
   make clean
   make install
   make test
   ```

2. **Manual Testing**
   - Test new functionality manually if applicable
   - Verify API endpoints with curl or Postman
   - Check GUI components if TechWF was modified

3. **Environment Verification**
   - Ensure `.env.example` includes any new environment variables
   - Document new configuration options
   - Test with clean environment

## Git Workflow
1. **Stage Changes Properly**
   ```bash
   git add <modified_files>
   # Don't use git add . blindly
   ```

2. **Write Descriptive Commit Message**
   - Use conventional commits format if applicable
   - Explain what was changed and why
   - Reference issue numbers if applicable

3. **Verify Clean Working Directory**
   ```bash
   git status
   # Ensure no untracked files or uncommitted changes remain
   ```

## Deployment Preparation
1. **Docker Build Test** (if applicable)
   ```bash
   make docker-build
   make docker-up
   # Test in containerized environment
   ```

2. **Production Configuration Review**
   - Check production environment variables
   - Verify security settings
   - Review resource requirements

## Quick Verification Command
```bash
# One-liner for basic quality check
make format && make lint && make test
```

This ensures code quality, functionality, and maintainability standards are met before considering the task complete.