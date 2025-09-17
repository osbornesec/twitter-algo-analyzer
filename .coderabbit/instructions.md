# CodeRabbit Review Instructions for Twitter Algorithm Analyzer

## Project Overview
This is a comprehensive Twitter data analysis system built with Python and Node.js, following Test-Driven Development (TDD) methodology. The project achieved 111/111 tests passing with comprehensive coverage.

## Key Components to Review

### 1. Authentication & Security (HIGH PRIORITY)
- **File**: `open_x_cdp.py`
  - Chrome DevTools Protocol integration for cookie extraction
  - Security of browser automation and data handling
  - Proper cleanup of browser sessions

- **File**: `twitter_client.py` (lines 56-85)
  - Cookie loading and validation logic  
  - Authentication state management
  - Secure handling of authentication tokens

- **Directory**: `twitter_bridge/middleware/`
  - Authentication middleware security
  - Input validation and sanitization
  - Rate limiting and abuse prevention

### 2. HTTP Client Reliability (MEDIUM PRIORITY)
- **File**: `twitter_client.py` (lines 87-144)
  - Error handling and retry logic with exponential backoff
  - Timeout configuration and connection management
  - Response validation and error propagation

### 3. Data Model Integrity (MEDIUM PRIORITY)
- **File**: `models.py`
  - Data validation in dataclass constructors
  - Type safety and field validation
  - Proper handling of missing/optional fields
  - Date parsing and timezone handling

- **File**: `twitter_client.py` (lines 146-231)
  - Response normalization logic
  - Data transformation accuracy
  - Error handling for malformed data

### 4. Test Coverage & Quality (HIGH PRIORITY)
- **File**: `tests/test_twitter_client.py`
  - Test completeness and edge case coverage
  - Proper mocking and isolation
  - Assertion quality and error scenarios
  - TDD methodology adherence

### 5. Node.js Bridge Security (HIGH PRIORITY)
- **Directory**: `twitter_bridge/routes/`
  - Endpoint security and validation
  - CORS configuration
  - Request/response sanitization
  - Error handling without information disclosure

## Review Focus Areas

### Security Checklist
- [ ] No hardcoded secrets or API keys
- [ ] Proper input validation on all endpoints
- [ ] Secure error handling (no sensitive info in errors)
- [ ] Authentication tokens handled securely
- [ ] HTTPS enforcement where applicable
- [ ] Rate limiting implemented

### Code Quality Checklist
- [ ] Follows Python PEP8 and Node.js best practices
- [ ] Functions are focused and not overly complex
- [ ] Proper error handling and logging
- [ ] Clear variable and function naming
- [ ] Adequate documentation and comments
- [ ] Type hints used appropriately (Python)

### Testing Checklist
- [ ] All new code has corresponding tests
- [ ] Tests cover edge cases and error scenarios
- [ ] Mocking is used appropriately for external dependencies
- [ ] Tests are independent and can run in any order
- [ ] Test names clearly describe what is being tested

### Performance Checklist
- [ ] No obvious performance bottlenecks
- [ ] Efficient data structures used
- [ ] Proper connection pooling and reuse
- [ ] Caching strategies where appropriate
- [ ] Memory usage considerations

## Files to Pay Special Attention To

1. **twitter_client.py** - Main client implementation with authentication and HTTP handling
2. **open_x_cdp.py** - Browser automation and cookie extraction
3. **models.py** - Data models and validation
4. **tests/test_twitter_client.py** - Comprehensive test suite
5. **twitter_bridge/middleware/auth.js** - Authentication middleware
6. **twitter_bridge/utils/response.js** - Response normalization

## Common Issues to Look For

1. **Authentication Issues**
   - Cookie expiration handling
   - Token refresh mechanisms
   - Secure storage of credentials

2. **Error Handling**
   - Proper exception propagation
   - Meaningful error messages
   - Graceful degradation

3. **Data Validation**
   - Input sanitization
   - Type checking
   - Boundary condition handling

4. **Resource Management**
   - Connection cleanup
   - Memory leaks
   - File handle management

## Severity Guidelines

- **CRITICAL**: Security vulnerabilities, data corruption risks
- **HIGH**: Authentication issues, test failures, major bugs
- **MEDIUM**: Performance issues, code quality concerns
- **LOW**: Style issues, minor optimizations, documentation

## Project Context
- Built using canonical TDD methodology
- 111/111 tests passing
- Production-ready code quality expected
- Security is paramount due to authentication handling
