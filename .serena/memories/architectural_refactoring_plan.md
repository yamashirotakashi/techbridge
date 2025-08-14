# TechWFMainWindow Architectural Refactoring Plan

## QualityGate Audit Finding
- **File**: `techwf/src/gui/main_window.py` (1,066 lines)
- **Issue**: Single Responsibility Principle violation
- **Current State**: 45+ methods in one class handling multiple concerns

## Refactoring Strategy
Split TechWFMainWindow into focused, single-responsibility classes following established patterns:

### 1. Core Window Management
**Class**: `TechWFMainWindow` (retain as main coordinator)
- Window lifecycle management
- Basic UI setup and layout
- Signal coordination between components
- Methods: `__init__`, `closeEvent`, `setup_signals`, `_setup_minimal_ui`

### 2. Service Integration Manager
**Class**: `TechWFServiceManager` 
- External service initialization and management
- Sheets, Slack, TSV import service coordination
- Methods: `_initialize_sheets_service`, `_initialize_slack_service`, `_update_sync_button_states`, `_update_slack_button_states`

### 3. Event Handler Coordinator
**Class**: `TechWFEventHandler`
- All event callback methods
- Data refresh and progress handling
- Methods: All `_on_*` methods (20+ methods)

### 4. Data Management Controller
**Class**: `TechWFDataController`
- Data loading, refreshing, and binding
- Methods: `load_initial_data`, `refresh_data`, `update_stats`, `_on_data_*` methods

### 5. Monitor Dashboard Manager
**Class**: `TechWFMonitorManager`
- Monitor dashboard integration and services
- Methods: `_integrate_monitor_dashboard`, `_initialize_monitor_services`, `_on_monitor_*` methods

### 6. UI Interaction Handler
**Class**: `TechWFUIInteractionHandler`
- Table interactions, selections, clicks
- Dialog management coordination
- Methods: `on_selection_changed`, `_on_table_*`, `on_cell_clicked`, `show_*` methods

## Implementation Approach
1. Create new manager classes in separate files
2. Extract methods maintaining their signatures
3. Update TechWFMainWindow to delegate to managers
4. Maintain existing public API for backward compatibility
5. Use dependency injection for manager coordination

## Expected Benefits
- **Maintainability**: Easier to modify specific functionality
- **Testability**: Each manager can be unit tested independently  
- **Readability**: Focused classes with clear responsibilities
- **Extensibility**: New features can be added to appropriate managers