# Git Workflow Rules

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/{issue}-{description}` | `feat/123-add-login` |
| Bugfix | `fix/{issue}-{description}` | `fix/456-null-check` |
| Chore | `chore/{description}` | `chore/update-deps` |
| Docs | `docs/{description}` | `docs/api-readme` |

## Commit Messages

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(auth): add OAuth2 login support

Implemented Google and GitHub OAuth2 providers.
- Added OAuth2 configuration
- Created callback handlers
- Updated user model

Closes #123
```

## Pull Requests

### Title Format
```
[TYPE] Brief description (#issue)
```

### Description Template
```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Test Plan
How to test these changes

## Screenshots (if UI)
```

## Safety Rules

- NEVER force push to main/master
- NEVER commit secrets or credentials
- ALWAYS create PR for main branch changes
- ALWAYS run tests before pushing
