# Coding Style Rules

## General Principles

- **Simplicity over cleverness** - Write code that's easy to understand
- **Consistency** - Follow existing patterns in the codebase
- **No over-engineering** - Only add complexity when necessary

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userName`, `totalCount` |
| Functions | camelCase | `getUserById()`, `calculateTotal()` |
| Classes | PascalCase | `UserService`, `DataProcessor` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| Files (JS/TS) | kebab-case | `user-service.ts`, `data-utils.js` |
| Files (Python) | snake_case | `user_service.py`, `data_utils.py` |

## Code Organization

### File Structure
```
src/
├── components/     # UI components
├── services/       # Business logic
├── utils/          # Helper functions
├── types/          # Type definitions
└── constants/      # Constants and configs
```

### Function Guidelines
- Single responsibility
- Max 30 lines preferred
- Early returns for guard clauses
- Descriptive names over comments

## Comments

- Write self-documenting code first
- Add comments for "why", not "what"
- Keep comments up-to-date with code
- Use JSDoc/docstrings for public APIs

## Error Handling

- Handle errors at appropriate level
- Provide meaningful error messages
- Log errors with context
- Don't swallow exceptions silently
