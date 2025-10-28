# B10 Backend Test Suite Documentation

## Overview

Comprehensive test suite for the Veda chatbot backend implementing Task B10 from the execution plan.

## Test Coverage

### 1. Unit Tests (`test_unit.py`)
Tests core utilities, authentication, and moderation functions without external dependencies.

**Coverage:**
- Password hashing and verification (bcrypt)
- JWT token creation and validation
- Content moderation rules
- Configuration loading
- Utility functions

**Run:**
```bash
pytest app/tests/B10_test/test_unit.py -v
```

### 2. CRUD Tests (`test_crud.py`)
Integration tests for database operations using SQLAlchemy ORM.

**Coverage:**
- User CRUD (Create, Read, Update, Delete)
- Conversation CRUD
- Message CRUD
- Cascade deletions
- Foreign key constraints
- Unique constraints

**Run:**
```bash
pytest app/tests/B10_test/test_crud.py -v
```

### 3. API Tests (`test_api.py`)
Integration tests for REST API endpoints.

**Coverage:**
- Authentication endpoints (register, login, refresh, /me)
- Conversation endpoints (list, create, get, delete)
- Message endpoints (list, create)
- Health check endpoint
- Authorization and access control

**Run:**
```bash
pytest app/tests/B10_test/test_api.py -v
```

### 4. WebSocket Tests (`test_websocket.py`)
Tests for real-time streaming functionality.

**Coverage:**
- WebSocket authentication
- Streaming chunks protocol
- Reconnection and idempotency
- Error handling
- Message format validation

**Run:**
```bash
pytest app/tests/B10_test/test_websocket.py -v
```

### 5. Pipeline Tests (`test_pipeline.py`)
Tests for LLM provider and multi-model orchestration.

**Coverage:**
- LLM provider with text input
- LLM provider with audio input
- LLM provider with image input
- Chat manager functionality
- RAG pipeline retrieval
- Model orchestration

**Run:**
```bash
pytest app/tests/B10_test/test_pipeline.py -v
```

### 6. Upload Tests (`test_uploads.py`)
Tests for file upload handling (images and audio).

**Coverage:**
- Image upload (PNG, JPEG, WebP)
- Audio upload (WAV, MP3)
- File size validation
- File type validation
- Security checks
- Audio transcription
- File cleanup

**Run:**
```bash
pytest app/tests/B10_test/test_uploads.py -v
```

### 7. Moderation Tests (`test_moderation.py`)
Tests for content safety and moderation.

**Coverage:**
- Safe content handling
- High severity blocking
- Medium severity flagging
- Case-insensitive matching
- Moderation rules loading
- Event logging
- Admin moderation views
- Emergency resources

**Run:**
```bash
pytest app/tests/B10_test/test_moderation.py -v
```

## Test Fixtures

### Database Fixtures
- `db_engine`: Module-scoped test database engine
- `db_session`: Function-scoped database session with cleanup
- `test_user`: Regular user for testing
- `admin_user`: Admin user for testing
- `test_conversation`: Test conversation
- `test_message`: Test message

### Authentication Fixtures
- `auth_headers`: Bearer token headers for regular user
- `admin_auth_headers`: Bearer token headers for admin user

### Utility Fixtures
- `tmp_upload_dir`: Temporary directory for file uploads
- `mock_llm_provider`: Mocked LLM provider for testing without model calls

## Running Tests

### Run All B10 Tests
```bash
cd backend
pytest app/tests/B10_test/ -v
```

### Run Specific Test File
```bash
pytest app/tests/B10_test/test_unit.py -v
```

### Run Specific Test Class
```bash
pytest app/tests/B10_test/test_api.py::TestAuthEndpoints -v
```

### Run Specific Test Function
```bash
pytest app/tests/B10_test/test_unit.py::TestPasswordHashing::test_hash_password -v
```

### Run with Coverage
```bash
pytest app/tests/B10_test/ --cov=app --cov-report=html
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Run everything except slow tests
pytest -m "not slow"
```

## Test Matrix

The test suite is designed to run across multiple environments:

### Python Versions
- Python 3.10
- Python 3.11

### Databases
- SQLite (in-memory) for fast tests
- PostgreSQL for integration tests

## Acceptance Criteria

✅ All tests pass locally
✅ Coverage ≥ 80% (configurable)
✅ Tests are isolated and idempotent
✅ Fixtures properly clean up resources
✅ Mock external dependencies (LLM, Pinecone)
✅ Tests are fast (< 30 seconds for full suite)

## CI Integration

Tests are automatically run in GitHub Actions on:
- Push to main branch
- Pull requests
- Pre-merge validation

## Test Data

### Mock LLM Responses
The `mock_llm_provider` fixture returns canned responses:
- Text input: "Mock response to: {text}"
- Audio input: "Mock response to audio input"
- Image input: "Mock response to image input"

### Test Users
- **Regular User**: test@example.com / testpassword123
- **Admin User**: admin@example.com / adminpassword123

### Moderation Keywords
Tests use the following keyword categories:
- **High Severity**: suicide, kill, bomb, violence
- **Medium Severity**: drug, prescription, weapon
- **Low Severity**: (testing only)

## Troubleshooting

### Database Errors
If you see "no such table" errors:
```bash
cd backend
alembic upgrade head
pytest app/tests/B10_test/ -v
```

### Import Errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Async Test Warnings
If you see async mode warnings, ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### WebSocket Test Skips
WebSocket tests may be skipped if the WebSocket endpoints are not fully implemented. This is expected during development.

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clean Fixtures**: Use function-scoped fixtures that clean up
3. **Mock External Services**: Don't call real APIs in tests
4. **Fast Tests**: Unit tests should run in milliseconds
5. **Descriptive Names**: Test names should describe what they test
6. **Arrange-Act-Assert**: Follow AAA pattern in tests

## Future Enhancements

- [ ] Add performance benchmarking tests
- [ ] Add load testing for WebSocket streaming
- [ ] Add security penetration tests
- [ ] Add E2E tests with real Ollama models
- [ ] Add mutation testing for coverage validation
- [ ] Add property-based tests with Hypothesis
- [ ] Add contract tests for API versioning

## Contributing

When adding new tests:
1. Place them in the appropriate test file
2. Use existing fixtures when possible
3. Add new fixtures to `conftest.py`
4. Update this documentation
5. Ensure tests are properly marked
6. Maintain high test quality and coverage
