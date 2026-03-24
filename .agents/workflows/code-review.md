---
description: Code review workflow — review code for quality, security, and maintainability
---

# Code Review Workflow

## Process

1. **Gather context** — Run `git diff --staged` and `git diff` to see all changes
2. **Understand scope** — Identify which files changed and how they connect
3. **Read surrounding code** — Don't review in isolation; understand imports, dependencies, call sites
4. **Apply checklist** — Work through each category below (CRITICAL → LOW)
5. **Report findings** — Only report issues you are >80% confident about

## Confidence-Based Filtering

- **Report** if >80% confident it is a real issue
- **Skip** stylistic preferences unless they violate project conventions
- **Skip** issues in unchanged code unless CRITICAL security issues
- **Consolidate** similar issues (e.g., "5 functions missing error handling")
- **Prioritize** bugs, security vulnerabilities, and data loss risks

## Review Checklist

### Security (CRITICAL)
- Hardcoded credentials (API keys, passwords, tokens)
- SQL injection (string concatenation in queries)
- XSS vulnerabilities (unescaped user input)
- Path traversal (user-controlled file paths)
- Authentication bypasses (missing auth checks)
- Exposed secrets in logs

### Code Quality (HIGH)
- Large functions (>50 lines) — split into smaller functions
- Large files (>800 lines) — extract modules
- Deep nesting (>4 levels) — use early returns
- Missing error handling — no empty catch blocks
- Mutation patterns — prefer immutable operations
- console.log / print statements — remove before merge
- Dead code — commented-out code, unused imports

### Python-Specific (HIGH)
- Bare `except: pass` — catch specific exceptions
- Mutable default arguments — `def f(x=[])` → use `None`
- Missing type hints on public functions
- `type() ==` instead of `isinstance()`
- String concatenation in loops — use `"".join()`
- Missing context managers — use `with` for resources
- `print()` instead of `logging`

### Performance (MEDIUM)
- O(n²) when O(n log n) or O(n) is possible
- Large imports (entire libraries when only a subset needed)
- Missing caching for repeated expensive computations
- Synchronous I/O in async contexts

### Best Practices (LOW)
- TODO/FIXME without issue references
- Missing docstrings on public APIs
- Magic numbers without named constants
- Inconsistent formatting

## Output Format

```
[SEVERITY] Issue title
File: path/to/file.py:42
Issue: Description
Fix: What to change
```

## Summary Table

End every review with:

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0     | pass   |
| HIGH     | 0     | pass   |
| MEDIUM   | 0     | info   |
| LOW      | 0     | note   |

**Verdict**: APPROVE / WARNING / BLOCK
- **Approve**: No CRITICAL or HIGH issues
- **Warning**: HIGH issues only (can merge with caution)
- **Block**: CRITICAL issues found — must fix before merge
