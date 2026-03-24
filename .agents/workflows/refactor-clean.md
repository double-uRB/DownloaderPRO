---
description: Dead code cleanup and refactoring workflow — safely remove unused code
---

# Refactor & Clean Workflow

## Workflow

### 1. Analyze
- Use `grep_search` and `find_by_name` to identify unused imports, functions, variables
- Categorize by risk:
  - **SAFE**: Unused private functions, unused imports, dead variables
  - **CAREFUL**: Dynamic imports, reflection-based usage
  - **RISKY**: Public API functions, exported symbols

### 2. Verify
For each item to remove:
- Grep for ALL references (including dynamic, string-based)
- Check if part of public API
- Review git history for context on why it exists

### 3. Remove Safely
- Start with SAFE items only
- Remove one category at a time: imports → functions → files → duplicates
- Run tests after each batch
- Commit after each batch with descriptive message

### 4. Consolidate Duplicates
- Find duplicate functions/modules
- Choose the best implementation (most complete, best tested)
- Update all references, delete duplicates
- Verify tests pass

## Safety Checklist

Before removing:
- [ ] Grep confirms no references (including dynamic/string-based)
- [ ] Not part of public API
- [ ] Tests pass after removal

After each batch:
- [ ] Build/run succeeds
- [ ] Tests pass
- [ ] Committed with descriptive message

## Key Principles

1. **Start small** — one category at a time
2. **Test often** — after every batch
3. **Be conservative** — when in doubt, don't remove
4. **Document** — descriptive commit messages per batch

## When NOT to Use

- During active feature development
- Right before production release
- Without proper test coverage
- On code you don't understand
