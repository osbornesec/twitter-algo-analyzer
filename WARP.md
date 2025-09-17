# WARP.md - Development Rules & Guidelines

## Project Overview

This is a Python-based AI algorithm system implementing Twitter/X content analysis and recommendation models using Test-Driven Development (TDD). The project provides data models, configuration management, and analysis tools for social media content evaluation.

## Core Architecture

- **Models** (`models.py`): Core data structures for tweets, profiles, engagement metrics, and recommendations
- **Configuration** (`config.py`): Configuration management with environment variable support
- **Tests** (`tests/`): Comprehensive test suite with fixtures and integration tests
- **Demo** (`demo.py`): Working demonstration of the TDD implementation

## Development Standards

### Code Quality Requirements

1. **Test-Driven Development (TDD)**
   - All new features must follow Red-Green-Refactor cycle
   - Write failing tests first, implement minimal code to pass, then refactor
   - Maintain 100% test coverage for core functionality
   - Use pytest for all testing

2. **Code Formatting & Linting**
   - Use Black for code formatting (line length: 88 characters)
   - Use Ruff for linting and import organization
   - Use MyPy for type checking with proper type annotations
   - All code must pass: `black --check .`, `ruff check .`, `mypy . --ignore-missing-imports --disable-error-code=import-untyped`

3. **Type Safety**
   - All functions must have proper type annotations
   - Use Optional[] for nullable fields
   - Use Union[] only when necessary, prefer specific types
   - Handle None values explicitly with null checks

### Python Standards

- **Python Version**: 3.12+
- **Virtual Environment**: Always use `venv/` for dependencies
- **Dependencies**: Listed in `requirements.txt`
- **Import Organization**: Group imports (stdlib, third-party, local) with blank lines
- **Docstrings**: Use triple quotes for all classes and functions
- **Error Handling**: Use specific exception types, validate inputs in `__post_init__`

### Data Models (`models.py`)

1. **Dataclass Usage**
   - Use `@dataclass` decorator for all data models
   - Implement `__post_init__` for validation
   - Provide both `from_dict()` and `to_dict()` methods for serialization

2. **Field Standards**
   - Use `field(default_factory=list)` for mutable defaults
   - Mark optional fields with `Optional[]` type hints
   - Validate required fields in `__post_init__`

3. **JSON Compatibility**
   - Support both camelCase (for JS clients) and snake_case (Python) field names
   - Normalize UTC timestamps to ISO format with 'Z' suffix (not '+00:00')
   - Handle timezone-naive datetimes by treating them as UTC

4. **Core Models**
   - `Tweet`: Main content model with engagement metrics and features
   - `Profile`: User profile information with influence calculations
   - `EngagementMetrics`: Likes, retweets, replies, views with rate calculations
   - `ContentFeatures`: Content analysis (sentiment, media, questions, etc.)
   - `Recommendation`: Action recommendations with confidence scoring

### Configuration Management (`config.py`)

1. **Environment Variables**
   - Support these environment variable mappings:
     - `API_BASE_URL` → `api['base_url']`
     - `TWITTER_BRIDGE_URL` → `api['base_url']` (alias)
     - `LOG_LEVEL` → `logging['level']`
     - `BATCH_SIZE` → `processing['batch_size']`
     - `LLM_PROVIDER` → `processing['llm']['provider']`

2. **Configuration Structure**
   - `PersonaConfig`: AI agent behavior and personality
   - `ScoringConfig`: Content evaluation weights and thresholds
   - `AppConfig`: Main application settings with API, logging, processing configs

3. **File Format Support**
   - Support both YAML (.yaml, .yml) and JSON (.json) configuration files
   - Deep-merge configuration sections to preserve default values
   - Validate URL formats, positive numeric values, and required fields

### Testing Standards (`tests/`)

1. **Test Organization**
   - `tests/test_models.py`: Model functionality and edge cases
   - `tests/test_config.py`: Configuration management and validation
   - `tests/fixtures/`: Sample data for integration testing

2. **Test Categories**
   - Unit tests for individual model methods
   - Integration tests using fixture data
   - Edge case testing (empty values, invalid inputs, etc.)
   - Serialization/deserialization compatibility tests

3. **Fixtures**
   - `tests/fixtures/sample_tweets.json`: Normalized tweet data structure
   - `tests/fixtures/sample_config.yaml`: Sample configuration with all sections

4. **Test Execution**
   - Use `PYTHONPATH=. pytest tests/ -v` for verbose test output
   - All tests must pass before committing changes
   - Use pytest fixtures for reusable test data

### File Structure Standards

```
/home/michael/dev/algo/
├── models.py              # Core data models
├── config.py              # Configuration management
├── demo.py                # Working demonstration
├── requirements.txt       # Python dependencies
├── WARP.md               # This rules file
├── venv/                 # Virtual environment (gitignored)
└── tests/
    ├── test_models.py    # Model tests
    ├── test_config.py    # Configuration tests
    └── fixtures/
        ├── sample_tweets.json    # Sample tweet data
        └── sample_config.yaml    # Sample configuration
```

## Development Workflow

### Pre-commit Checklist

1. **Code Quality**: Run all formatting and linting tools
   ```bash
   black .
   ruff check . --fix
   source venv/bin/activate && mypy . --ignore-missing-imports --disable-error-code=import-untyped
   ```

2. **Testing**: Ensure all tests pass
   ```bash
   source venv/bin/activate && PYTHONPATH=. pytest tests/ -v
   ```

3. **Functionality**: Test core features work as expected
   ```bash
   source venv/bin/activate && python demo.py
   ```

### Adding New Features

1. **Follow TDD Cycle**:
   - Red: Write failing tests for new functionality
   - Green: Implement minimal code to make tests pass
   - Refactor: Improve code quality while keeping tests green

2. **Update Documentation**: Add docstrings and update WARP.md if needed

3. **Maintain Compatibility**: Ensure JSON serialization remains compatible with Node.js bridge

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional type stubs if needed
pip install types-python-dateutil

# Run tests to verify setup
PYTHONPATH=. pytest tests/ -v
```

## Integration Requirements

### Node.js Bridge Compatibility

- Maintain camelCase field names in JSON serialization
- Use 'Z' suffix for UTC timestamps (not '+00:00')
- Support nested object structures for engagement and features
- Handle both snake_case and camelCase in `from_dict()` methods

### Data Contracts

- Tweet IDs must be strings (not integers)
- Engagement metrics must be non-negative integers
- Sentiment must be one of: "positive", "negative", "neutral"
- Priority levels must be one of: "high", "medium", "low"
- Action types for recommendations: "like", "retweet", "reply", "follow", "unfollow", "mute", "block"

## Performance Guidelines

- Use `field(default_factory=...)` for mutable default values
- Implement lazy evaluation where appropriate (e.g., age calculations)
- Cache expensive computations in data model methods
- Use efficient data structures (lists for ordered data, dicts for lookups)

## Security Considerations

- Validate all input data in `__post_init__` methods
- Use URL validation for API endpoints
- Handle environment variables safely (no secrets in plain text)
- Sanitize user-provided content appropriately

## Error Handling

- Use specific exception types (`ValueError`, `FileNotFoundError`, etc.)
- Provide descriptive error messages with context
- Handle edge cases gracefully (empty inputs, missing fields)
- Log errors appropriately based on configured log level

## Version Compatibility

- Python 3.12+ required
- Compatible with pytest 8.4+, mypy 1.17+, black 25.1+, ruff 0.13+
- All dependencies specified in requirements.txt with version constraints

## Contributing Guidelines

1. **Branch Naming**: Use descriptive branch names (e.g., `feature/scoring-algorithm`, `fix/timezone-handling`)
2. **Commit Messages**: Use clear, descriptive commit messages
3. **Pull Requests**: Include test coverage and documentation updates
4. **Code Reviews**: All changes require code review and passing CI checks

---

This WARP.md file should be updated as the project evolves. When adding new features or changing architecture, update the relevant sections to maintain consistency across the development team.