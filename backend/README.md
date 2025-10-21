# Veda Backend

Healthcare chatbot API built with FastAPI, PostgreSQL, and async SQLAlchemy.

## Features

- ✅ FastAPI with async support
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ JWT authentication with refresh tokens
- ✅ Google OAuth2 integration (planned)
- ✅ WebSocket streaming for chat
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
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/veda
JWT_SECRET=your-secret-key-here
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
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

### Current (Phase B00)

- `GET /` - Root endpoint with API info
- `GET /health` - Health check endpoint

### Planned

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Send message
- `WS /ws/conversations/{id}` - WebSocket streaming

## Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py
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

## Development Notes

### Phase B00 - Backend Scaffold + Health ✅

**Completed:**
- ✅ Created backend directory structure
- ✅ Added requirements.txt with all dependencies
- ✅ Implemented FastAPI app with health endpoint
- ✅ Added CORS middleware for frontend
- ✅ Created __init__.py files for Python packages
- ✅ Server starts successfully and serves /health endpoint

**Acceptance Criteria:**
- ✅ `uvicorn app.main:app --reload` serves /health endpoint with 200 status

### Next Steps (Phase B01)

- [ ] Implement config module (core/config.py)
- [ ] Implement security module (core/security.py)
- [ ] Set up async database session (db/session.py)
- [ ] Configure Alembic for migrations

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
