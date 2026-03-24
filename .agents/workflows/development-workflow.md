---
description: Research-first development workflow — search, plan, TDD, review, commit
---

# Development Workflow

Follow this pipeline for every feature or significant code change.

## 0. Research & Reuse (MANDATORY before coding)

1. **Search the codebase first** — use `grep_search` and `find_by_name` to find existing implementations
2. **Search package registries** — check PyPI, npm, etc. for battle-tested libraries before writing utility code
3. **Search the web** — use `search_web` for broader research when codebase and docs are insufficient
4. **Check for adaptable implementations** — look for open-source projects that solve 80%+ of the problem
5. **Decision matrix:**
   - Exact match, well-maintained → **Adopt** (install and use directly)
   - Partial match, good foundation → **Extend** (install + thin wrapper)
   - Nothing suitable → **Build** (write custom, informed by research)

## 1. Plan First

- Create an implementation plan before coding
- Identify dependencies and risks
- Break down into independently deliverable phases
- Use `/plan` workflow for detailed planning

## 2. TDD Approach

- Write tests first (RED)
- Implement to pass tests (GREEN)
- Refactor (IMPROVE)
- Verify 80%+ coverage
- Use `/tdd` workflow for guidance

## 3. Code Review

- Review immediately after writing code
- Use `/code-review` workflow
- Address CRITICAL and HIGH issues before proceeding
- Fix MEDIUM issues when possible

## 4. Security Check

- Run `/security-review` for any code handling user input, auth, API endpoints, or secrets
- Fix all CRITICAL security issues before commit

## 5. Commit & Push

- Use conventional commits: `<type>: <description>`
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- Analyze full commit history with `git diff` before creating PR summary
- Push with `-u` flag if new branch
