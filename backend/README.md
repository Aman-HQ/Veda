# Veda Backend

Healthcare chatbot API built with FastAPI, PostgreSQL, and async SQLAlchemy.

## Features

- ✅ FastAPI with async support
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ JWT authentication with refresh tokens
- ✅ Google OAuth2 integration
- ✅ WebSocket streaming for chat
- ✅ Multi-model orchestration (Ollama + Pinecone RAG)
- ✅ Content moderation and safety
- ✅ Admin dashboard with comprehensive statistics
- ✅ Structured logging with log rotation
- ✅ Prometheus metrics integration
- ✅ System resource monitoring
- ✅ Health check endpoint
- ✅ CORS configured for frontend

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Configuration & security
│   ├── db/                  # Database connection & session
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── crud/                # CRUD operations
│   ├── api/                 # API routes
│   │   └── routers/
│   ├── services/            # Business logic
│   │   └── rag/            # RAG pipeline
│   └── tests/               # Tests
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
└── .gitignore
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Virtual environment (recommended)

### Installation

1. **Create and activate virtual environment:**

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies:**

```powershell
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file in the backend directory (copy from `.env.example`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/veda
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=veda
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Authentication
JWT_SECRET=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5173/oauth/callback

# Ollama (LLM)
OLLAMA_URL=http://localhost:11434
OLLAMA_API_KEY=

# Pinecone (Vector DB)
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=your-pinecone-env
PINECONE_INDEX=veda-index

# Features
ENABLE_MODERATION=true
ENABLE_METRICS=true
DEBUG=true
```

4. **Run database migrations:**

```powershell
alembic upgrade head
```

## Running the Server

### Development (with auto-reload)

```powershell
# From the backend directory
$env:PYTHONPATH = "d:\chatbot\Veda\backend"
Set-Location d:\chatbot\Veda\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or simply:

```powershell
uvicorn app.main:app --reload
```

The server will start at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Production

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Available Endpoints

### Core

- `GET /` - Root endpoint with API info
- `GET /health` - Enhanced health check with database status
- `GET /docs` - Interactive API documentation
- `GET /metrics` - Prometheus metrics (when ENABLE_METRICS=true)

### Authentication (B04)

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `GET /api/auth/google/login` - Google OAuth2 login
- `GET /api/auth/google/callback` - Google OAuth2 callback

### Conversations (B06)

- `GET /api/conversations` - List user's conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}` - Get conversation details
- `DELETE /api/conversations/{id}` - Delete conversation

### Messages (B06)

- `GET /api/conversations/{id}/messages` - Get conversation messages
- `POST /api/conversations/{id}/messages` - Send message (text, image, audio)

### Streaming (B07)

- `WS /ws/conversations/{id}?token={jwt}` - WebSocket streaming chat

### Admin & Observability (B09)

- `GET /api/admin/stats` - Comprehensive system statistics
- `GET /api/admin/metrics` - Real-time metrics (uptime, active conversations, etc.)
- `GET /api/admin/moderation/stats` - Moderation statistics
- `POST /api/admin/moderation/reload-rules` - Reload moderation rules
- `GET /api/admin/users` - List all users (paginated)
- `GET /api/admin/conversations/flagged` - Get flagged conversations
- `GET /api/admin/system/health` - System health check
- `POST /api/admin/users/{user_id}/role` - Update user role

**Note:** All admin endpoints require admin role authentication.

## Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run B09 tests (Admin & Observability)
pytest app/tests/B09_test/ -v

# Run async tests
pytest --asyncio-mode=auto
```

## Database Management

### Create migration

```powershell
alembic revision --autogenerate -m "description"
```

### Apply migrations

```powershell
alembic upgrade head
```

### Rollback migration

```powershell
alembic downgrade -1
```

## Logging and Monitoring

### Log Files

All logs are stored in the `logs/` directory:

- **app.log** - General application logs (10 MB rotation, 7 days retention)
- **error.log** - Errors and exceptions only (5 MB rotation, 14 days retention)
- **moderation.log** - Content moderation events (5 MB rotation, 30 days retention, JSON format)
- **admin.log** - Admin actions and system events (5 MB rotation, 30 days retention, JSON format)

### Viewing Logs

```powershell
# View live application logs
Get-Content logs\app.log -Wait -Tail 50

# View error logs only
Get-Content logs\error.log -Wait -Tail 50

# View moderation events (JSON format, requires jq)
Get-Content logs\moderation.log | ConvertFrom-Json

# Search for specific events
Select-String "flagged" logs\moderation.log
```

### Prometheus Metrics

When `ENABLE_METRICS=true`, Prometheus metrics are available at `/metrics`:

```powershell
# Access metrics
curl http://localhost:8000/metrics

# Configure Prometheus to scrape this endpoint
# Add to prometheus.yml:
# scrape_configs:
#   - job_name: 'veda-backend'
#     static_configs:
#       - targets: ['localhost:8000']
```

### Admin Dashboard

Access admin statistics and metrics (requires admin role):

```powershell
# Get comprehensive statistics
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/admin/stats

# Get real-time metrics
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/admin/metrics

# Check system health
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/admin/system/health
```

## Development Notes

### Completed Phases

#### Phase B00 - Backend Scaffold + Health ✅
- ✅ Created backend directory structure
- ✅ Added requirements.txt with all dependencies
- ✅ Implemented FastAPI app with health endpoint
- ✅ Added CORS middleware for frontend

#### Phase B01 - Config, Security, DB ✅
- ✅ Config module with environment variables
- ✅ Security module with JWT and password hashing
- ✅ Async database session with PostgreSQL

#### Phase B02 - Database Migrations (Alembic) ✅
- ✅ Alembic configured for async SQLAlchemy
- ✅ Migration scripts for all models

#### Phase B03 - Models & Schemas ✅
- ✅ User, Conversation, Message ORM models
- ✅ Pydantic schemas for validation
- ✅ Model relationships and constraints

#### Phase B04 - Auth Endpoints ✅
- ✅ Email/password registration and login
- ✅ JWT access and refresh tokens
- ✅ Google OAuth2 integration

#### Phase B05 - FastAPI Integration ✅
- ✅ SQLAlchemy async sessions
- ✅ Dependency injection for database
- ✅ Error handling and validation

#### Phase B06 - Conversations & Messages CRUD ✅
- ✅ Full CRUD for conversations
- ✅ Full CRUD for messages
- ✅ User-specific data access

#### Phase B07 - Streaming (WebSocket) ✅
- ✅ WebSocket authentication
- ✅ Token streaming with chunk/done protocol
- ✅ Reconnection and idempotency

#### Phase B07.5 - Multi-Model Orchestration ✅
- ✅ Ollama integration (Whisper, Llama, MedGemma)
- ✅ Pinecone RAG pipeline
- ✅ LangChain integration
- ✅ Multi-step processing (STT → summarize → RAG → answer)

#### Phase B08 - Moderation & Safety ✅
- ✅ Keyword-based content moderation
- ✅ Severity-based flagging (high/medium/low)
- ✅ Flagged message tracking
- ✅ Admin logs for violations

#### Phase B09 - Admin & Observability ✅
- ✅ Admin statistics endpoint with comprehensive metrics
- ✅ Real-time metrics (uptime, conversations, messages, resources)
- ✅ Structured logging with loguru (app.log, error.log, moderation.log, admin.log)
- ✅ Log rotation (10 MB) and retention (7-30 days)
- ✅ Prometheus metrics integration
- ✅ System resource monitoring (CPU, memory)
- ✅ Role-based access control for admin endpoints
- ✅ Comprehensive test suite (989 lines, 100% coverage)

### Next Steps (Phase B010)

- [ ] Backend integration tests
- [ ] End-to-end test scenarios
- [ ] Performance benchmarking
- [ ] Load testing

## Troubleshooting

### ModuleNotFoundError: No module named 'app'

Make sure you're running uvicorn from the backend directory:

```powershell
Set-Location d:\chatbot\Veda\backend
python -m uvicorn app.main:app --reload
```

### Port already in use

Kill the process using port 8000 or use a different port:

```powershell
# Use different port
uvicorn app.main:app --reload --port 8001
```

### Import errors

Make sure all dependencies are installed:

```powershell
pip install -r requirements.txt
```

## Contributing

See the main project README and docs/plan.md for development guidelines.

## License

[Add your license here]
