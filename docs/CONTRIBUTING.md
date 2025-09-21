# Contributing Guide

## Getting Started

### Development Environment
1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Follow [DEVELOPMENT.md](./DEVELOPMENT.md) for local setup
4. Create a feature branch: `git checkout -b feature/your-feature`

### Code Standards

#### Python (Backend/ML)
- **Style**: Black formatter + isort
- **Linting**: flake8 with max line length 88
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public methods

```python
def process_paper(paper_data: Dict[str, Any]) -> ProcessedPaper:
    """Process a research paper for clustering and analysis.
    
    Args:
        paper_data: Raw paper metadata from arXiv or other sources
        
    Returns:
        ProcessedPaper object with embeddings and extracted features
        
    Raises:
        ValidationError: If paper data is invalid
    """
```

#### TypeScript (Frontend)
- **Style**: Prettier with 2-space indentation
- **Linting**: ESLint with strict TypeScript rules
- **Components**: Functional components with hooks
- **Testing**: Jest + React Testing Library

### Commit Guidelines

#### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes (if needed)

Closes #issue-number
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `perf`: Performance improvements

#### Examples
```
feat(ml): add BERT-based paper clustering algorithm

Implement hierarchical clustering using SciBERT embeddings
for improved research paper grouping accuracy.

Closes #123
```

### Testing Requirements

#### Backend Tests
```bash
# Unit tests (required for all new code)
pytest backend/tests/unit/

# Integration tests (required for API changes)
pytest backend/tests/integration/

# Coverage requirement: >90%
pytest --cov=backend --cov-report=html
```

#### ML Model Tests
```bash
# Model accuracy tests
pytest ml-service/tests/test_clustering.py
pytest ml-service/tests/test_summarization.py

# Performance benchmarks
pytest ml-service/tests/test_performance.py
```

#### Frontend Tests
```bash
# Component tests
npm test

# E2E tests (for major features)
npm run test:e2e
```

### Pull Request Process

#### Before Submitting
1. **Run all tests**: Ensure 100% test pass rate
2. **Check code quality**: Run linters and formatters
3. **Update documentation**: Add/update relevant docs
4. **Performance check**: Verify no significant performance regression

#### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Performance Impact
- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance regression (explain)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
```

### Feature Development Guidelines

#### New ML Models
1. **Research Phase**: Document model selection rationale
2. **Implementation**: Follow existing model structure
3. **Evaluation**: Include benchmark comparisons
4. **Documentation**: Add model cards and usage examples

#### API Changes
1. **Backward Compatibility**: Maintain existing endpoints
2. **Versioning**: Use semantic versioning for breaking changes
3. **Documentation**: Update OpenAPI specs
4. **Testing**: Add comprehensive integration tests

#### Frontend Features
1. **Accessibility**: Follow WCAG 2.1 AA guidelines
2. **Performance**: Optimize for Core Web Vitals
3. **Responsive Design**: Support mobile and desktop
4. **User Testing**: Include usability considerations

### Code Review Process

#### Reviewer Guidelines
- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code readable and maintainable?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security vulnerabilities?
- **Testing**: Is the code adequately tested?

#### Review Checklist
- [ ] Code follows project conventions
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Accessibility requirements met

### Issue Reporting

#### Bug Reports
```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v1.2.3]

**Additional Context**
Screenshots, logs, etc.
```

#### Feature Requests
```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches considered

**Additional Context**
Mockups, examples, etc.
```

### Documentation Standards

#### API Documentation
- Use OpenAPI 3.0 specifications
- Include request/response examples
- Document error codes and messages
- Provide usage examples

#### Code Documentation
- Document all public APIs
- Include usage examples
- Explain complex algorithms
- Document configuration options

#### User Documentation
- Step-by-step tutorials
- Screenshots for UI features
- Troubleshooting guides
- FAQ sections

### Release Process

#### Version Numbering
- **Major**: Breaking changes (v2.0.0)
- **Minor**: New features (v1.1.0)
- **Patch**: Bug fixes (v1.0.1)

#### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Performance benchmarks run
- [ ] Security scan completed
- [ ] Deployment tested in staging

### Community Guidelines

#### Code of Conduct
- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers get started
- Focus on technical merit

#### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code review and discussion