---
description: Test-driven development workflow — write tests first, then implement
---

# TDD Workflow

## Red-Green-Refactor Cycle

### 1. Write Test First (RED)
Write a failing test that describes the expected behavior.

### 2. Run Test — Verify it FAILS
```bash
pytest
```

### 3. Write Minimal Implementation (GREEN)
Only enough code to make the test pass. Nothing more.

### 4. Run Test — Verify it PASSES
```bash
pytest
```

### 5. Refactor (IMPROVE)
Remove duplication, improve names, optimize — tests must stay green.

### 6. Verify Coverage
```bash
pytest --cov=src --cov-report=term-missing
# Required: 80%+ branches, functions, lines
```

## Test Types Required

| Type | What to Test | When |
|------|-------------|------|
| **Unit** | Individual functions in isolation | Always |
| **Integration** | API endpoints, database operations | Always |
| **E2E** | Critical user flows | Critical paths |

## Edge Cases You MUST Test

1. **None/null** input
2. **Empty** lists/strings/dicts
3. **Invalid types** passed
4. **Boundary values** (min/max, 0, negative)
5. **Error paths** (network failures, file not found)
6. **Race conditions** (concurrent operations)
7. **Large data** (performance with 10k+ items)
8. **Special characters** (Unicode, path separators, quotes)

## Test Anti-Patterns to Avoid

- Testing implementation details instead of behavior
- Tests depending on each other (shared state)
- Asserting too little (tests that pass vacuously)
- Not mocking external dependencies
- Using `time.sleep()` instead of proper waits

## Quality Checklist

- [ ] All public functions have unit tests
- [ ] Edge cases covered (None, empty, invalid)
- [ ] Error paths tested (not just happy path)
- [ ] Mocks used for external dependencies
- [ ] Tests are independent (no shared state)
- [ ] Assertions are specific and meaningful
- [ ] Coverage is 80%+
