# Architecture Patterns Guide

Reference for system design, architecture decisions, and common patterns.

## Architecture Principles

### 1. Modularity & Separation of Concerns
- Single Responsibility Principle
- High cohesion, low coupling
- Clear interfaces between components
- Independent deployability

### 2. Scalability
- Horizontal scaling capability
- Stateless design where possible
- Efficient database queries
- Caching strategies

### 3. Maintainability
- Clear code organization
- Consistent patterns
- Comprehensive documentation
- Easy to test

### 4. Security
- Defense in depth
- Principle of least privilege
- Input validation at boundaries
- Secure by default

## Common Patterns

### Frontend
- **Component Composition**: Build complex UI from simple components
- **Container/Presenter**: Separate data logic from presentation
- **Code Splitting**: Lazy load routes and heavy components

### Backend
- **Repository Pattern**: Abstract data access behind a consistent interface
- **Service Layer**: Business logic separation from controllers
- **Middleware Pattern**: Request/response processing pipeline
- **Event-Driven Architecture**: Async operations via events

### Data
- **Normalized Database**: Reduce redundancy
- **Caching Layers**: Redis, CDN for read-heavy operations
- **Eventual Consistency**: For distributed systems

## Architecture Decision Records (ADRs)

For significant decisions, use this template:

```markdown
# ADR-NNN: [Decision Title]

## Context
[Why was this decision needed?]

## Decision
[What was decided?]

## Consequences

### Positive
- [Benefit 1]

### Negative
- [Drawback 1]

### Alternatives Considered
- [Alternative 1]: [Why rejected]

## Status
Accepted / Proposed / Deprecated

## Date
YYYY-MM-DD
```

## System Design Checklist

### Functional Requirements
- [ ] User stories documented
- [ ] API contracts defined
- [ ] Data models specified

### Non-Functional Requirements
- [ ] Performance targets defined (latency, throughput)
- [ ] Security requirements identified
- [ ] Availability targets set

### Technical Design
- [ ] Architecture diagram created
- [ ] Component responsibilities defined
- [ ] Data flow documented
- [ ] Error handling strategy defined
- [ ] Testing strategy planned

### Operations
- [ ] Deployment strategy defined
- [ ] Monitoring planned
- [ ] Rollback plan documented

## Red Flags (Anti-Patterns)

| Anti-Pattern | Description | Fix |
|---|---|---|
| Big Ball of Mud | No clear structure | Define module boundaries |
| Golden Hammer | Same solution for everything | Evaluate alternatives |
| Premature Optimization | Optimizing too early | Profile first, optimize later |
| God Object | One class does everything | Split by responsibility |
| Tight Coupling | Components too dependent | Use interfaces/abstractions |
| Magic | Undocumented behavior | Document or simplify |
