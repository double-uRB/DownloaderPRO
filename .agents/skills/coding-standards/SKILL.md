---
name: coding-standards
description: Coding style, file organization, error handling, and quality standards for writing clean, maintainable code. Combines coding style rules, design patterns, and performance guidelines.
---

# Coding Standards

Universal coding standards and quality guidelines for all projects.

## When to Activate

- Writing new code in any language
- Reviewing code quality
- Refactoring for clarity and maintainability
- Setting up a new project or module

## Immutability (CRITICAL)

ALWAYS create new objects, NEVER mutate existing ones:

```python
# WRONG: Mutation
user["name"] = "Alice"  # modifies original dict

# CORRECT: Create new copy
updated_user = {**user, "name": "Alice"}  # returns new dict
```

Rationale: Immutable data prevents hidden side effects, makes debugging easier, and enables safe concurrency.

## File Organization

MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

## Error Handling

ALWAYS handle errors comprehensively:
- Handle errors explicitly at every level
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Never silently swallow errors

```python
# BAD: Bare except
try:
    risky_operation()
except:
    pass  # Silent failure!

# GOOD: Specific exceptions with logging
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

## Input Validation

ALWAYS validate at system boundaries:
- Validate all user input before processing
- Use schema-based validation where available (Pydantic, Zod)
- Fail fast with clear error messages
- Never trust external data (API responses, user input, file content)

## Functions

- Keep functions under 50 lines
- Single responsibility — one function does one thing
- Use descriptive names: `calculate_total_price()` not `calc()`
- Limit parameters to 5 max; use dataclass/dict for more
- Use early returns to reduce nesting

```python
# BAD: Deep nesting
def process(users):
    if users:
        for user in users:
            if user.active:
                if user.email:
                    send_email(user)

# GOOD: Early returns + flat
def process(users):
    if not users:
        return
    active_with_email = [u for u in users if u.active and u.email]
    for user in active_with_email:
        send_email(user)
```

## Design Patterns

### Repository Pattern
Encapsulate data access behind a consistent interface:
- Define standard operations: `find_all`, `find_by_id`, `create`, `update`, `delete`
- Business logic depends on the abstract interface, not storage mechanism
- Enables easy testing with mocks

### API Response Format
Use a consistent envelope for all API responses:
- Include a success/status indicator
- Include the data payload (nullable on error)
- Include an error message field (nullable on success)
- Include metadata for paginated responses (total, page, limit)

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation (immutable patterns used)
- [ ] Input validated at boundaries
- [ ] No debug print/log statements left
- [ ] No commented-out code
