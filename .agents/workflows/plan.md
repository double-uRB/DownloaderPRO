---
description: Feature planning workflow — create detailed implementation plans with architecture review
---

# Planning Workflow

## Planning Process

### 1. Requirements Analysis
- Understand the feature request completely
- Ask clarifying questions if needed
- Identify success criteria
- List assumptions and constraints

### 2. Research & Architecture Review
- Search codebase for existing patterns and similar implementations
- Identify affected components
- Consider reusable patterns
- Evaluate trade-offs for each design decision

### 3. Step Breakdown
Create detailed steps with:
- Clear, specific actions
- File paths and locations
- Dependencies between steps
- Estimated complexity (Low/Medium/High)
- Potential risks

### 4. Implementation Order
- Prioritize by dependencies
- Group related changes
- Minimize context switching
- Enable incremental testing

## Plan Template

```markdown
# Implementation Plan: [Feature Name]

## Overview
[2-3 sentence summary]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Architecture Changes
- [Change 1: file path and description]

## Implementation Steps

### Phase 1: [Phase Name]
1. **[Step Name]** (File: path/to/file.py)
   - Action: Specific action to take
   - Why: Reason for this step
   - Dependencies: None / Requires step X
   - Risk: Low/Medium/High

### Phase 2: [Phase Name]
...

## Testing Strategy
- Unit tests: [files to test]
- Integration tests: [flows to test]

## Risks & Mitigations
- **Risk**: [Description]
  - Mitigation: [How to address]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## Sizing and Phasing

For large features, break into independently deliverable phases:
- **Phase 1**: Minimum viable — smallest slice that provides value
- **Phase 2**: Core experience — complete happy path
- **Phase 3**: Edge cases — error handling, polish
- **Phase 4**: Optimization — performance, monitoring

Each phase should be mergeable independently.

## Architecture Decision Records

For significant decisions, document:
- **Context**: Why was this decision needed?
- **Decision**: What was decided?
- **Consequences**: Positive, negative, and alternatives considered

## Best Practices

1. **Be Specific** — use exact file paths, function names
2. **Consider Edge Cases** — error scenarios, null values, empty states
3. **Minimize Changes** — prefer extending existing code over rewriting
4. **Maintain Patterns** — follow existing project conventions
5. **Enable Testing** — structure changes to be easily testable
6. **Think Incrementally** — each step should be verifiable
