# Best Practices Guide

Condensed reference for development best practices across coding, testing, security, and workflow.

## Coding Style

- **Immutability**: Always create new objects instead of mutating existing ones
- **Small files**: 200-400 lines typical, 800 max. Many small files > few large files
- **Small functions**: <50 lines. Single responsibility
- **No deep nesting**: Max 4 levels. Use early returns
- **Explicit errors**: Never silently swallow exceptions
- **No magic numbers**: Use named constants
- **No hardcoded secrets**: Always use environment variables

## Development Workflow

```
Research → Plan → TDD → Code Review → Security Check → Commit
```

1. **Search first** — check codebase, libraries, and web before writing
2. **Plan** — create implementation plan with phases and risks
3. **Write tests first** — RED-GREEN-REFACTOR cycle
4. **Review** — use code review checklist (CRITICAL → LOW)
5. **Security scan** — check OWASP Top 10 before commit
6. **Commit** — conventional commits: `feat:`, `fix:`, `refactor:`, etc.

## Git Workflow

### Commit Format
```
<type>: <description>

<optional body>
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

### PR Process
1. Analyze full commit history (`git diff base...HEAD`)
2. Draft comprehensive PR summary
3. Include test plan
4. Push with `-u` flag for new branches

## Testing Standards

- **Minimum coverage**: 80%
- **Test types**: Unit (always), Integration (always), E2E (critical paths)
- **TDD mandatory**: Write tests first, then implement
- **Edge cases**: None/null, empty, invalid types, boundaries, error paths
- **Test isolation**: No shared state between tests
- **Mock externals**: Always mock APIs, databases, file systems

## Security Essentials

- No hardcoded secrets — use environment variables
- Validate all user inputs with schemas
- Use parameterized queries (never string concatenation in SQL)
- Sanitize HTML output (prevent XSS)
- Check authentication on every protected route
- Add rate limiting to API endpoints
- Don't expose internal errors to users
- Don't log sensitive data (passwords, tokens, PII)

## Performance

- Prefer efficient algorithms (O(n) over O(n²))
- Use generators/iterators for large datasets
- Cache expensive computations
- Avoid string concatenation in loops — use `join()`
- Lazy load when possible
- Profile before optimizing

## File Organization

```
project/
├── src/               # Source code
│   ├── core/          # Core business logic
│   ├── api/           # API endpoints
│   ├── models/        # Data models
│   └── utils/         # Utilities
├── tests/             # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/            # Configuration
├── docs/              # Documentation
└── scripts/           # Build/deploy scripts
```

Organize by feature/domain, not by file type.
