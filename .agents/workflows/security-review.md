---
description: Security audit workflow — OWASP Top 10, secrets detection, vulnerability remediation
---

# Security Review Workflow

Run this workflow when writing code that handles user input, authentication, API endpoints, secrets, or sensitive data.

## 1. Initial Scan

- Search for hardcoded secrets: `grep_search` for API keys, passwords, tokens, connection strings
- Review high-risk areas: auth, API endpoints, DB queries, file uploads, payments, webhooks
- Check dependencies for known vulnerabilities

## 2. OWASP Top 10 Check

1. **Injection** — Queries parameterized? User input sanitized? ORMs used safely?
2. **Broken Auth** — Passwords hashed (bcrypt/argon2)? JWT validated? Sessions secure?
3. **Sensitive Data** — HTTPS enforced? Secrets in env vars? PII encrypted? Logs sanitized?
4. **XXE** — XML parsers configured securely? External entities disabled?
5. **Broken Access** — Auth checked on every route? CORS properly configured?
6. **Misconfiguration** — Default creds changed? Debug mode off in prod? Security headers set?
7. **XSS** — Output escaped? CSP set? Framework auto-escaping?
8. **Insecure Deserialization** — User input deserialized safely?
9. **Known Vulnerabilities** — Dependencies up to date?
10. **Insufficient Logging** — Security events logged? Alerts configured?

## 3. Code Pattern Review

Flag these patterns immediately:

| Pattern | Severity | Fix |
|---------|----------|-----|
| Hardcoded secrets | CRITICAL | Use environment variables |
| Shell command with user input | CRITICAL | Use safe APIs or subprocess with list args |
| String-concatenated SQL | CRITICAL | Parameterized queries |
| `innerHTML = userInput` | HIGH | Use `textContent` or sanitization |
| `fetch(userProvidedUrl)` | HIGH | Whitelist allowed domains |
| Plaintext password comparison | CRITICAL | Use `bcrypt.compare()` or equivalent |
| No auth check on route | CRITICAL | Add authentication middleware |
| No rate limiting | HIGH | Add rate limiting |
| Logging passwords/secrets | MEDIUM | Sanitize log output |

## 4. Mandatory Pre-Commit Checklist

- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] Authentication/authorization verified
- [ ] Error messages don't leak sensitive data
- [ ] No sensitive data in logs

## 5. Emergency Response Protocol

If CRITICAL vulnerability found:
1. STOP immediately
2. Document with detailed report
3. Provide secure code example
4. Verify remediation works
5. Rotate any exposed secrets
6. Review entire codebase for similar issues
