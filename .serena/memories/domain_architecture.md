# TechBridge Domain Architecture

## Current Architecture Overview

TechBridge follows a layered architecture with clear separation of concerns:

### Layer Structure
1. **API Layer** (`app/api/`): HTTP endpoints and request handling
2. **Service Layer** (`app/services/`): Business logic implementation  
3. **CRUD Layer** (`app/crud/`): Database operations
4. **Model Layer** (`app/models/`): Data models and domain entities
5. **Schema Layer** (`app/schemas/`): Request/response validation

## Domain Entities

### Core Workflow Domain
- **WorkflowItem**: Central entity representing a book in the publication workflow
- **ProgressStatus**: Enum defining workflow stages with state transition logic
- **WorkflowStatus**: Additional status tracking (referenced in models)

### Integration Domains
- **Slack Integration**: Bot functionality and notifications
- **Google Sheets Integration**: Spreadsheet synchronization
- **External Services**: Webhook handling and API integration

## Business Logic Distribution

### Current State (Analysis)
Based on the codebase examination, business logic is currently distributed across:

1. **Models** (`app/models/workflow.py`):
   - `WorkflowItem` entity with basic field definitions
   - Database relationships and constraints

2. **Enums** (`app/models/enums.py`):
   - `ProgressStatus` with rich behavior:
     - Display name and emoji methods
     - State transition logic (`get_next_status()`)
     - Validation logic (`can_transition_to()`)

3. **Services** (`app/services/`):
   - Business logic scattered across service files
   - External integration handling
   - Workflow management operations

4. **TechWF Component** (`techwf/`):
   - Separate GUI application with its own domain logic
   - Complex workflow orchestration
   - File watching and external service coordination

## Identified Business Logic for Extraction

### Book Domain Logic
- Book discovery and metadata management
- Publication status tracking and validation
- Progress calculation and reporting
- Author and publisher information handling

### Workflow Domain Logic  
- Stage transition management and validation
- Business rule enforcement
- Deadline and scheduling logic
- Error handling and recovery procedures

### Integration Domain Logic
- External service coordination
- Webhook processing and validation  
- Notification and communication rules
- Data synchronization between systems

## Architecture Goals for Stage 2A

The Business Logic Extraction phase should focus on:

1. **Pure Domain Services**: Extract UI-independent business logic
2. **Testable Functions**: Create easily testable pure functions
3. **Domain Model Enhancement**: Enrich domain entities with behavior
4. **Service Layer Cleanup**: Separate coordination from business rules

## Target Domain Structure

### Proposed Domain Services
- `BookDomainService`: Book-related business logic
- `WorkflowDomainService`: Workflow management logic
- `IntegrationDomainService`: External system coordination rules

### Implementation Principles
- **Immutability**: Domain operations return new states
- **Pure Functions**: No side effects in domain logic
- **Type Safety**: Strong typing and validation
- **Testability**: Easy unit testing without infrastructure dependencies

## Integration Points

### Current Integration Complexity
The system integrates with multiple external services:
- Slack API for notifications
- Google Sheets for data synchronization  
- Webhook endpoints for external triggers
- File system monitoring for automated workflows

### Domain Logic Separation Strategy
- Extract business rules from integration code
- Create domain events for external system triggers
- Implement domain validation independent of external data formats
- Design contracts between domain and infrastructure layers

This architecture analysis provides the foundation for implementing the Business Logic Extraction phase of the Domain-Driven Design refactoring.