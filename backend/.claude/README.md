# Backend Development Standards

## Overview

This directory contains mandatory development standards for the AI Code Modernizer backend. All code must comply with these standards.

## Standards Documents

### 1. Agentic Security (`.claude/agentic-security.md`)
**When to read**: Before implementing any agent, tool, or LLM integration

Critical security guidelines for AI agent development:
- Principle of least privilege for agent tool access
- Input validation and sanitization
- Prompt injection prevention
- Tool call validation
- Docker isolation for code execution
- Rate limiting and resource controls
- Secrets management (no API keys in logs)
- Audit logging for all agent actions
- Error handling without information disclosure
- Human-in-the-loop for critical operations
- Security testing patterns
- Threat model and defense layers

**Key Principle**: Never execute user code on host system. Always use Docker isolation.

### 2. Python Standards (`.claude/python-standards.md`)
**When to read**: Before writing any Python code

Python best practices and patterns:
- PEP 8 compliance with specific formatting rules
- Type hints for all function signatures
- Google-style docstrings with examples
- Custom exception hierarchy
- Specific exception handling (no bare except)
- Context managers for resource cleanup
- Dataclasses and TypedDict usage
- Properties and private methods
- Async/await patterns for I/O operations
- Pytest conventions and fixtures
- Performance optimization (caching, lazy loading)
- Structured logging standards

**Key Principle**: Every component must have `if __name__ == "__main__"` block for standalone testing.

### 3. API Design Standards (`.claude/api-design-standards.md`)
**When to read**: Before implementing or modifying API endpoints

API design and implementation guidelines:
- RESTful URL structure (resource-based, not action-based)
- Appropriate HTTP methods and status codes
- Pydantic models for request/response validation
- Consistent response format across endpoints
- Global exception handling
- Authentication and authorization patterns
- Rate limiting implementation
- API versioning strategy
- WebSocket standards for real-time updates
- Comprehensive OpenAPI documentation
- Request/response examples

**Key Principle**: All endpoints must return consistent response format with proper status codes.

### 4. Testing Standards (`.claude/testing-standards.md`)
**When to read**: Before writing tests or new features

Comprehensive testing guidelines:
- Test structure and organization
- Test naming conventions
- Unit test isolation with fixtures
- Mocking external dependencies
- Parametrized tests for multiple scenarios
- Integration testing (API, database, workflow)
- End-to-end testing
- Test fixtures and helpers
- Performance testing
- Coverage requirements (>80%)

**Key Principle**: Tests must be isolated, independent, and use proper mocking.

## Quick Reference

### Security Checklist (Before Committing)
- [ ] Agent has minimal required tool access
- [ ] All inputs validated and sanitized
- [ ] System prompts protected from injection
- [ ] Tool calls validated before execution
- [ ] Code execution only in Docker
- [ ] No secrets in logs or errors
- [ ] Audit logging implemented
- [ ] Human approval for critical operations

### Code Quality Checklist (Before Committing)
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Custom exceptions for domain errors
- [ ] Context managers for resources
- [ ] Private methods prefixed with `_`
- [ ] Properties for computed attributes
- [ ] Tests cover happy path and errors
- [ ] Structured logging with context
- [ ] PEP 8 compliant

### API Checklist (Before Deploying)
- [ ] RESTful URL structure
- [ ] Proper HTTP methods and status codes
- [ ] Pydantic models for validation
- [ ] Consistent response format
- [ ] Global exception handling
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] OpenAPI documentation

### Testing Checklist (Before PR)
- [ ] Unit tests for new code
- [ ] Integration tests for workflows
- [ ] Tests are isolated and independent
- [ ] Mocks used for external dependencies
- [ ] Coverage >80%
- [ ] All tests pass
- [ ] Performance tests if applicable

## Enforcement

These standards are **mandatory** and will be enforced through:
1. Code review - All PRs must comply
2. Automated checks - CI/CD pipeline validates standards
3. Testing requirements - Coverage and test patterns enforced

## When to Reference

| Task | Read These Documents |
|------|---------------------|
| Implementing new agent | `agentic-security.md`, `python-standards.md` |
| Adding new tool | `agentic-security.md`, `python-standards.md` |
| Creating API endpoint | `api-design-standards.md`, `python-standards.md` |
| Writing tests | `testing-standards.md`, `python-standards.md` |
| LangGraph workflow | `agentic-security.md`, `python-standards.md` |
| Error handling | `agentic-security.md`, `api-design-standards.md` |
| Authentication | `agentic-security.md`, `api-design-standards.md` |

## Examples

Each standards document contains:
- ✅ **CORRECT** examples showing the right way
- ❌ **INCORRECT** examples showing what to avoid
- Detailed explanations of why patterns matter
- Security implications
- Performance considerations

## Getting Help

If a standard is unclear or seems impractical for your use case:
1. Review the examples in the relevant document
2. Check for similar patterns in existing code
3. Discuss with team before deviating from standards
4. Document exceptions with clear reasoning

## Updates

These standards are living documents. When updating:
1. Ensure consistency across all documents
2. Add examples for new patterns
3. Update quick reference checklists
4. Notify team of changes
