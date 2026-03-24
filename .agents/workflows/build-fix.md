---
description: Build error resolution workflow — fix build/type errors with minimal diffs
---

# Build Fix Workflow

Fix build errors with minimal changes — no refactoring, no architecture changes.

## 1. Collect All Errors
- Run the build/compile command and capture all errors
- Categorize: type errors, missing imports, config issues, dependency problems
- Prioritize: build-blocking first, then warnings

## 2. Fix Strategy (MINIMAL CHANGES)

For each error:
1. Read the error message carefully — understand expected vs actual
2. Find the minimal fix (type annotation, null check, import fix)
3. Verify fix doesn't break other code — rebuild
4. Iterate until build passes

## 3. Common Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Install package or fix import path |
| `ImportError` | Check module name, verify installation |
| `TypeError` | Add type conversion or fix argument types |
| `AttributeError` | Check object has attribute, add null check |
| `SyntaxError` | Fix syntax (missing colon, bracket, etc.) |
| `IndentationError` | Fix indentation (spaces vs tabs) |
| `NameError` | Define variable or fix spelling |
| `FileNotFoundError` | Check path, create missing file/dir |

## DO and DON'T

**DO:**
- Add missing imports
- Fix type mismatches
- Add null/None checks where needed
- Install missing dependencies
- Fix configuration files

**DON'T:**
- Refactor unrelated code
- Change architecture
- Rename variables (unless causing error)
- Add new features
- Optimize performance or style

## Quick Recovery

```bash
# Python: Reinstall dependencies
pip install -r requirements.txt

# Python: Clear cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Node: Reinstall dependencies
rm -rf node_modules && npm install
```

## Success Metrics

- Build/run completes without errors
- No new errors introduced
- Minimal lines changed
- Tests still passing
