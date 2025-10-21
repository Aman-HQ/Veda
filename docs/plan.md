# Veda Chatbot — Execution Plan

**Purpose:** Turn the roadmap into a concrete, sequenced plan with unambiguous steps, commands, and acceptance criteria.
**Rules:** JS React frontend (Vite), FastAPI backend, PostgreSQL (SQLAlchemy + async driver), TailwindCSS, JWT + Google OAuth2, REST + WebSocket streaming, Dockerized local dev, no OpenAI API.

---

## Scope and assumptions

- **Frontend:** React (Vite) + JavaScript only, TailwindCSS, Jest + React Testing Library
- **Backend:** FastAPI (async), Pydantic, PostgreSQL via SQLAlchemy (async + Alembic for migrations)
- **Auth:** JWT access + refresh, Google OAuth2
- **Communication:** REST for CRUD, WebSocket for streaming
- **LLM:** Custom fine‑tuned local/service model integrated via `llm_provider.py` abstraction
- **Containers:** Docker + docker-compose
- **OS:** Windows 10/11 dev experience friendly, PowerShell commands shown
- **Docs:** `docs/plan.md`
- **Frontend-first:** Build full UI with mocks → then backend → integrate → harden.

---

## 1.Environments

### 1.1 Docker Compose Setup

Below is an example `docker-compose.yml` for local development:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15
    container_name: veda_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    container_name: veda_backend
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    container_name: veda_frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:

```

### 1.2 Environment variables (.env.example)

**Backend:**

# -------------------------------
# Ollama Configuration
# -------------------------------
OLLAMA_URL=http://localhost:11434          # Change if Ollama runs elsewhere
OLLAMA_API_KEY=                            # Optional if Ollama requires an API key

# -------------------------------
# Pinecone Configuration
# -------------------------------
PINECONE_API_KEY=
PINECONE_ENV=                              # Example: us-west1-gcp
PINECONE_INDEX=veda-index

# -------------------------------
# PostgreSQL Configuration
# -------------------------------
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=veda
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# -------------------------------
# Authentication & Security
# -------------------------------
JWT_SECRET=replace_me
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# -------------------------------
# Google OAuth Configuration
# -------------------------------
GOOGLE_CLIENT_ID=replace_me
GOOGLE_CLIENT_SECRET=replace_me
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5173/oauth/callback

# -------------------------------
# LLM / AI Provider Configuration
# -------------------------------
LLM_PROVIDER=local
LLM_ENDPOINT=http://llm:8080
ENABLE_MODERATION=true
ENABLE_METRICS=false

**Secrets Handling**
- Do not commit `.env` to git. Add `.env` to `.gitignore`.
- For production, use a secrets manager (AWS Secrets Manager / Vault / GitHub Secrets) and avoid plaintext env files.


**Frontend:**

```
VITE_API_BASE=http://localhost:8000
VITE_WS_BASE=ws://localhost:8000
VITE_GOOGLE_CLIENT_ID=replace_me
```

### 1.3 Running Locally

- Copy `.env.example` to `.env` and fill in the missing values.
- Start all services:
   ```bash
   docker-compose up --build


## 2. Directory Guardrails (target structure)

```
veda/
├─ .env.example
├─ docker-compose.yml
├─ docker/
│  ├─ backend.Dockerfile
│  └─ frontend.Dockerfile
├─ README.md
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ tailwind.config.cjs
│  ├─ postcss.config.cjs
│  ├─ public/
│  │  └─ vite.svg
|  ├─ index.html
│  └─ src/
│     ├─ main.jsx
│     ├─ App.jsx
│     ├─ index.css
│     ├─ pages/
│     │  ├─ Login.jsx
│     │  ├─ Register.jsx
│     │  ├─ Home.jsx
│     │  └─ ChatPage.jsx
│     ├─ components/
│     │  ├─ Layout/
│     │  │  ├─ Topbar.jsx
│     │  │  └─ Sidebar.jsx
│     │  ├─ Chat/
│     │  │  ├─ ChatLayout.jsx
│     │  │  ├─ ConversationList.jsx
│     │  │  ├─ ChatWindow.jsx
│     │  │  ├─ MessageBubble.jsx
│     │  │  ├─ Composer.jsx
│     │  │  ├─ TypingIndicator.jsx
│     │  │  ├─ ImageUploader.jsx
│     │  │  └─ VoiceInput.jsx
│     │  └─ Common/
│     │     ├─ Button.jsx
│     │     ├─ Modal.jsx
│     │     └─ Icon.jsx
│     ├─ hooks/
│     │  ├─ useAuth.js
│     │  ├─ useWebSocket.js
│     │  └─ useDebounce.js
│     ├─ services/
│     │  ├─ api.js
│     │  └─ chatService.js
│     ├─ stores/
│     │  ├─ authStore.js
│     │  └─ uiStore.js
│     ├─ utils/
│     │  ├─ formatDate.js
│     │  └─ sanitizeHtml.js
│     ├─ assets/
│     └─ tests/
│        └─ ChatWindow.test.jsx
└─ backend/
   ├─ app/
   │  ├─ main.py
   │  ├─ core/
   │  │  ├─ config.py
   │  │  └─ security.py
   │  ├─ db/
   │  │  ├─ base.py        # SQLAlchemy Base + metadata
   │  │  ├─ session.py     # async engine & session
   │  │  └─ init_db.py     # Alembic migration setup or initial create_all()
   │  ├─ models/
   │  │  ├─ user.py
   │  │  ├─ conversation.py
   │  │  └─ message.py
   │  ├─ schemas/
   │  │  ├─ auth.py
   │  │  └─ chat.py
   │  ├─ crud.py
   │  │  ├─ user_crud.py
   │  │  ├─ conversation_crud.py
   │  │  └─ message_crud.py
   │  ├─ api/
   │  │  ├─ deps.py
   │  │  └─ routers/
   │  │     ├─ auth.py
   │  │     ├─ users.py
   │  │     ├─ conversations.py
   │  │     ├─ messages.py
   │  │     └─ stream.py
   │  ├─ services/
   │  │  ├─ llm_provider.py   # orchestrates which model to call and in what order
   │  │  ├─ chat_manager.py   # handles conversation flow and WebSocket streaming
   │  │  └─ rag/
   │  │     └─ pipeline.py   # LangChain RAG integration
   │  └─ tests/
   │     └─ test_auth.py
   ├─ alembic/
   │  ├─ env.py
   │  ├─ script.py.mako
   │  └─ versions/
   ├─ requirements.txt
   └─ Dockerfile

```

## 3. Phased plan (Strict Sequence)

### Phase F — Frontend First (UI + mocks)

#### F00 — Repo setup and quality gates (frontend)

**Actions**

- Initialize git repo structure
- Add `docs/` with `roadmap.md` and `plan.md`
- Prettier + ESLint configuration (JS only)
- Add `.editorconfig`
- Create `.env.example`
- Define npm scripts for lint/test

**Commands(PowerShell)**

```powershell
cd .\veda
git init
echo "root = true`n[*]`nindent_style = space`nindent_size = 2" > .editorconfig
```

**Acceptance**

- Running `npm run lint` in `frontend/` passes (baseline)

#### F01 — Vite App + Tailwind + Router + Axios

**Actions**

- Create app (if not already): vite react
- Install deps: tailwind, postcss, autoprefixer, react-router-dom, axios
- Init Tailwind and wire index.css

**Commands(PowerShell)**

```powershell
cd .\veda
npm create vite@latest frontend -- --template react
cd .\frontend
npm i tailwindcss postcss autoprefixer react-router-dom axios
npx tailwindcss init -p
npm i -D eslint prettier eslint-config-prettier eslint-plugin-react eslint-plugin-react-hooks
```

**Acceptance**

- App boots at http://localhost:5173, Tailwind classes render.

#### F02 — Frontend Structure & Routing

**Actions**

- Create all folders & empty files inside frontend/src/: (see Directory Guardrails)
- Setup BrowserRouter in main.jsx
- Define routes in App.jsx: /login, /register, /chat (Home can redirect to /chat)

**Acceptance**

- Navigating routes switches pages (basic placeholders visible).

#### F03 — Core Layout (Topbar, Sidebar, Chat Scaffolding)

**Actions**

- Implement responsive shell in `ChatPage.jsx` using `ChatLayout.jsx`
- Add `Topbar.jsx`, `Sidebar.jsx` with placeholders
- Keyboard handling outline in `Composer.jsx` (Enter send, Shift+Enter newline)

**Acceptance**

- Mobile/desktop responsive splits; no console errors.

#### F04 — Auth UI + Store (Mock)

**Actions**

- Build `Login.jsx`, `Register.jsx` forms (email, password, name)
- Add `authStore.js` (in-memory accessToken; refreshToken in localStorage mock only)
- Add `useAuth.js` (helpers: login, logout, register, isAuthed)
- Add placeholder Google button (reads `VITE_GOOGLE_CLIENT_ID`)
- Route guards; redirect to `ChatPage` after login

**Acceptance**

- “Login” sets mock auth state and redirects to /chat.

#### F05 — Chat UI Components + Mock Data

**Actions**

- Responsive layout with sidebar and chat window
- Components: `ConversationList`, `ChatWindow`, `MessageBubble`, `Composer`, `TypingIndicator`, `ImageUploader`, `VoiceInput`
- Keyboard handling (Enter=send, Shift+Enter=newline)
- Light gradient background; mobile and desktop views
- Create services/mockApi.js to simulate:
  - listConversations(), createConversation(), deleteConversation()
  - listMessages(conversationId), createMessage()
- Wire UI to mockApi via chatService.js (toggle with VITE_USE_MOCK_API)

**Acceptance**

- Switching conversations updates the chat window
- Selecting conversations renders messages; sending message appends mock reply (delayed).

#### F06 — WebSocket Hook (Mock)

**Actions**

- Implement useWebSocket.js with interface:
  connect(token, conversationId), onChunk(cb), onDone(cb), onError(cb), disconnect()
- Add mock implementation that emits chunks from a static string to drive UI
- In ChatWindow, render streamed partials, then finalize message

**Acceptance**

- Live token streaming visible in UI; partial → final message transition works
- WebSocket reconnect resumes safely without duplicating messages

#### F07 — UX Polish + Accessibility + Disclaimer

**Actions**

- Gradient background, focus states, ARIA labels on buttons/inputs
- Append static healthcare disclaimer to assistant bubbles in UI
- Collapsible sidebar on mobile

**Acceptance**

- Keyboard navigable; disclaimer consistently visible on assistant messages.

#### F08 — Utilities, Stores, Services Hardening

**Actions**

- uiStore.js: sidebar state, active conversation, modals
- utils/formatDate.js, utils/sanitizeHtml.js (basic)
- services/api.js: Axios instance (reads VITE_API_BASE), auth header injection (from store)

**Acceptance**

- No errors; all modules imported where needed; mocks still active.

#### F09 — Frontend Tests

**Actions**

- Add Jest + RTL; write tests for:
- ChatWindow rendering stream partials → final
- Composer submit behaviors
- Conversation switching renders correct messages

**Commands(PowerShell)**

```powershell
cd .\frontend
npm i -D jest @testing-library/react @testing-library/jest-dom @testing-library/user-event vite-jest
```

**Acceptance**

- npm test passes locally.

---

**FrontEnd Done Criteria**

- Routing solid (/login, /register, /chat)
- Full chat UI working with mock REST + mock WebSocket
- Disclaimer shown on assistant messages
- Basic tests green

---

### Phase B — Backend (APIs, Auth, Models, Streaming)

#### B00 — Backend Scaffold + Health

**Actions**

- Create backend/ with FastAPI layout (`app/` tree as in guardrails(target structure))
- App factory in `app/main.py`
- Add `/health` endpoint
- Add requirements.txt (fastapi, uvicorn, pydantic, sqlalchemy[asyncio], asyncpg, alembic, bcrypt, python-jose[cryptography], python-multipart, httpx)

**Development Dependencies (for PostgreSQL setup):**
```bash
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg alembic bcrypt python-jose[cryptography] python-multipart
```
**(Dev/test optional)**
```bash
pip install pytest pytest-asyncio httpx
```

**Acceptance**

- `uvicorn app.main:app --reload` serves /health 200.

#### B01 — Config, Security, DB

**Reference example  Directory Guardrails (target structure) for backend setup:**

**Actions**

- Config module `core/config.py`: load envs, CORS origins

**Example (`app/config.py`):**

```python
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/veda"
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "veda-index")
```
- Security module `core/security.py`: password hash/verify (bcrypt), JWT create/verify, token payloads
- db/session.py: create async engine and sessionmaker

**Example (`app/db.py`)**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

# Create async engine (future=True recommended)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```
```md
Notes:
- `expire_on_commit=False` avoids expired objects; `autoflush=False` is optional.
- Use `async with session.begin():` in handlers to ensure commit/rollback semantics when grouping operations.
```
- db/base.py: define declarative base for models
- db/init_db.py: initialize database, optionally run alembic upgrade head


**Acceptance**

- Startup logs show PostgreSQL connected; tables created or migrations applied.

#### B02 — Database Migrations (Alembic)

**Actions**
- Initialize Alembic in backend/
```python
cd backend
alembic init alembic
```
**Alembic + Async note**
- For autogenerate with async SQLAlchemy:
  Use a sync engine in `alembic/env.py` for autogenerate by replacing `+asyncpg` in DATABASE_URL (easiest)

- Configure `alembic.ini` with `sqlalchemy.url = DATABASE_URL`
- Generate migration scripts with `alembic revision --autogenerate -m "init"`
- Apply migrations using `alembic upgrade head`

***Example (alembic/env.py) adjustments for async engine:***

```python
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from app.db import Base
from app.config import DATABASE_URL

# ... usual config loading ...
target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(
        DATABASE_URL.replace('+asyncpg', ''),  # sync engine for autogenerate
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```
```md
Then create & apply:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```
**Acceptance**
- Tables created via Alembic; migration history tracked.


#### B03 — Models & Schemas (PostgreSQL + SQLAlchemy)

**Actions**

- Create ORM models inheriting from `Base` (SQLAlchemy declarative base):
  - **User** → id (UUID PK), email (unique), hashed_password, name, role, refresh_tokens (JSON), created_at
  - **Conversation** → id (UUID PK), user_id (FK to users.id), title, messages_count, created_at
  - **Message** → id (UUID PK), conversation_id (FK to conversations.id), sender ("user"/"assistant"), content, status, metadata (JSON), created_at
- Add relationships:
  - `User.conversations = relationship("Conversation", back_populates="user")`
  - `Conversation.messages = relationship("Message", back_populates="conversation")`
- Update Pydantic schemas in `schemas/` to mirror ORM fields.
- Use `func.now()` for timestamps, `UUID` for IDs, and async session commits.

**Example (`app/models.py`)**
```python
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    name = Column(String(256), nullable=True)
    role = Column(String(50), default="user")
    refresh_tokens = Column(JSON, default=list)  # store refresh tokens metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=True)
    messages_count = Column(String, default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(TEXT, nullable=False)
    status = Column(String(50), default="sent")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

```

**Acceptance**

- ORM models map correctly; basic CRUD works in shell.
- ORM models load correctly, Alembic generates migration, and test inserts/queries work 

#### B04 — Auth Endpoints (Email/Password + Google OAuth2)

**Actions**

- Implement endpoints `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me` using async SQLAlchemy sessions.
- Replace Beanie calls like `await User.find_one(User.email == email)` with SQLAlchemy queries:
  ```python
  result = await session.execute(select(User).where(User.email == email))
  user = result.scalars().first()
    ```
- For inserts(user creation):
  ```python
new_user = User(email=email, hashed_password=hashed, name=name)
session.add(new_user)
await session.commit()
await session.refresh(new_user)
    ``` 
- Passwords hashed using bcrypt (same as before)
- Tokens (JWT) logic unchanged — reuse security.py
- Google OAuth: `/api/auth/google/login` (redirect URL), `/api/auth/google/callback`
- Issue access (short) + refresh (long) tokens
- CORS configured for http://localhost:5173

**Acceptance**

- Register/login/refresh round-trip; /me authorized with Bearer token.
- Google flow completes locally (or feature-flag if creds not yet ready).
- Google OAuth provides a session and redirects to `ChatPage`
- Register/login/refresh flows work end-to-end against PostgreSQL (SQLAlchemy)
- `Authorization: Bearer <access>` applied to protected API calls; auto‑refresh on 401
- Database inserts/queries verified through SQLAlchemy sessions.

#### B05 — FastAPI Integration 
```md
This clarifies how the backend integrates with SQLAlchemy.
This clarifies how to configure Alembic for PostgreSQL + async setup.

**Example (`app/main.py`):**
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .db import engine, Base, get_db
from .models import User, Message, Conversation

app = FastAPI()

@app.on_event("startup")
async def startup():
    # For development only: create tables if not present.
    # Prefer alembic for production migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/chat")
async def chat(username: str, user_message: str, db: AsyncSession = Depends(get_db)):
    # Save user message (use transaction)
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalars().first()

    if not user:
        user = User(email=username)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # create conversation if needed (simple example)
    # For demo, create or reuse a default conversation:
    conv = Conversation(user_id=user.id, title="Default")
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    # Add user message
    msg = Message(conversation_id=conv.id, sender="user", content=user_message)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Generate response (your LLM call)
    response = "This is where your model reply goes."

    bot_msg = Message(conversation_id=conv.id, sender="assistant", content=response)
    db.add(bot_msg)
    await db.commit()
    await db.refresh(bot_msg)

    return {"response": response}

``` 

#### B06 — Conversations & Messages CRUD

**Actions**

- Implement endpoints using SQLAlchemy ORM + async session:
  - **Conversations**
    - GET: `select(Conversation).where(Conversation.user_id == current_user.id)`
    - POST: create new conversation (insert → commit → refresh)
    - DELETE: delete by `conversation_id`
  - **Messages**
    - GET: list messages by `conversation_id`
    - POST: insert new message with `conversation_id` FK
- Define relationships between models:
  - `Conversation.user_id → users.id`
  - `Message.conversation_id → conversations.id`
- Remove Mongo indexes section — PostgreSQL automatically indexes PK/FK; add manual indexes only if needed.
- Update Pydantic schemas for consistency with ORM models.

---
**CRUD patterns Example:**

**Get a conversation list for user:**
```python
from sqlalchemy import select

async def list_conversations(user_id, db: AsyncSession):
    result = await db.execute(select(Conversation).where(Conversation.user_id == user_id))
    return result.scalars().all()
```
**Insert message with transaction**
```python
async def create_message(conversation_id, sender, content, db: AsyncSession):
    async with db.begin():
        msg = Message(conversation_id=conversation_id, sender=sender, content=content)
        db.add(msg)
    # After context, transaction committed
    await db.refresh(msg)
    return msg
```

**Acceptance**

- CRUD operations persist and retrieve conversations/messages via PostgreSQL.
- Foreign keys and cascading deletes validated through Alembic migrations.


#### B07 — Streaming (WebSocket)

**Actions**

- ws://.../ws/conversations/{id}?token=<JWT> authenticates, streams chunks
- Stream Protocol:
  ```json
  { "type": "chunk", "messageId": "...", "data": "..." }
  { "type": "done", "message": { "id": "...", "content": "..." } }
  { "type": "error", "error": "..." }
  ```
- services/llm_provider.py: start with echo/markov dev mode
- services/chat_manager.py: enqueue user msg, stream assistant, persist partials, finalize

**Example (in router):(`api/routers/messages.py`)**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.chat_manager import ChatManager

router = APIRouter()

@router.post("/{conversation_id}/messages")
async def create_message(conversation_id: str, payload: dict, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    text = payload.get("text")
    audio = payload.get("audio")  # binary or base64 if implemented
    image = payload.get("image")  # base64 or URL
    manager = ChatManager(db)
    answer = await manager.handle_user_message(conversation_id, user.id, text=text, audio=audio, image=image)
    return {"answer": answer}
```

- Extend payload to support image input (`payload["image"]` as base64 or multipart).  
  `ChatManager.handle_user_message` should forward `image` to `llm_provider.process_pipeline(image=...)` when provided.
- Inside `llm_provider.py`, detect `image` input and call appropriate Ollama multimodal model (e.g., `llava` or `bakllava`) before summarization or final response.

- Append server-side health disclaimer to assistant messages

**NOTE**
For WebSocket flow, call ChatManager.handle_user_message and forward streaming via the ws connection (use ws_streamer that wraps websocket.send_json for chunk/done).

**WebSocket Auth & Reconnect**
- Connection URL: `ws://host/ws/conversations/{id}?token=<JWT>`
- On connect: validate JWT (same as HTTP auth) and check conversation access.
- Reconnect/backoff: client backoff: 1s, 2s, 4s, 8s, max 30s. Server accepts reconnects; use `client_message_id` to deduplicate.
- Idempotency: each user message has client-provided `client_message_id` (UUID). Server checks and ignores duplicates.

**Streaming Tokenization & Persistence Details**
- For Ollama or LLM models that support streaming, use incremental JSON lines or event-stream responses.
- `chat_manager.py` should forward each token/chunk to WebSocket clients immediately:
  ```python
  async for chunk in ollama_stream(model="medgemma-4b-it", prompt=prompt):
      await ws_streamer.send_chunk(conv_id, chunk)
  await ws_streamer.send_done(conv_id)
  ```
- Each chunk should also be appended to an in-memory buffer; at done, persist the full message content to DB via create_message().
- Store partial tokens only in RAM; avoid partial DB writes to reduce transaction overhead.
- If stream fails mid-way, emit { "type": "error", "error": "stream interrupted" } and save partial message with "incomplete": true.

**Acceptance**

- Test client receives chunked tokens → final; 
- DB contains full thread.

#### B07.5 — Multi-Model Orchestration (LLM Pipeline)

**Purpose**
- Orchestrate multiple specialized models (STT, summarizer, RAG, main answerer) using **Ollama** as the unified model host and **Pinecone** as the vector DB for RAG. All orchestration is done server-side via `llm_provider.py` called from `chat_manager.py`.

**Actions**
- Update `core/config.py` to include Ollama + Pinecone settings (OLLAMA_URL, OLLAMA_API_KEY optional, PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX).
- Keep `services/llm_provider.py` as the single orchestrator. Implement Ollama calls inside this file 
- Add `services/rag/pipeline.py` to implement LangChain-style retrieval from Pinecone (vector index) and return ranked context docs.
- Implement `services/chat_manager.py` to:
  - persist user messages,
  - call `llm_provider.process_pipeline(audio=None, image=None, text=None, opts={})`,
  - stream tokens back to the frontend using the existing WebSocket chunk/done protocol,
  - persist assistant message(s) after finished/partially while streaming if desired.
- Provide dev-mode toggles in config to run a canned-responses mode for unit tests.
- Add minimal test coverage for the pipeline where model calls are mocked/canned.

**Design notes**
- **Ollama**: use Ollama's local HTTP API or Python client (via async HTTP client like `httpx`) to call different model names (e.g., `whisper`, `llama-3.2`, `medgemma-4b-it`) sequentially from inside `llm_provider.process_pipeline`.
- **RAG**: `services/rag/pipeline.py` should expose `async def retrieve(query, top_k=5)` that queries Pinecone (via Pinecone client or LangChain retriever), returns context docs used by the final model prompt.
```md
**Pinecone Embeddings & Indexing**
- Decide embedding provider (i.e,Ollama embeddings). Add env var EMBED_PROVIDER.
- Store embeddings with metadata: `{id, text, source, created_at}`.
- Ingestion pipeline:
  1. Extract text → 2. Compute embedding via EMBED_PROVIDER → 3. upsert to Pinecone index with metadata.
- Include sample embed command in docs and add `scripts/seed_vector_index.py`.
```

- **Orchestration**: Typical pipeline: `audio -> (Whisper) -> text -> (Llama summarizer) -> summary -> (RAG retrieve) -> docs -> (MedGemma) -> final_answer`.
- Use config flags to skip steps (e.g., `SKIP_SUMMARIZER=true`) or to select alternative models.

**Files to create**
- `backend/app/services/llm_provider.py`  # calls Ollama API and orchestrates pipeline
- `backend/app/services/chat_manager.py`  # chat flow + streaming integration
- `backend/app/services/rag/pipeline.py`  # LangChain/Pinecone retriever wrapper

**Minimal code: Ollama (async) + Pinecone RAG sketch**

Note: Ollama doesn’t have an official async SDK (use httpx to call the local Ollama REST API). These examples use httpx (async).

**Example-(`app/services/llm_provider.py`)**
```python
import os
import httpx
from typing import Optional, List, Dict
from .rag.pipeline import RAGPipeline
from app.core.config import OLLAMA_URL, OLLAMA_API_KEY  # update config to export these

OLLAMA_URL = OLLAMA_URL  # e.g. "http://localhost:11434"

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_URL, api_key: Optional[str] = None):
        self.base = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def chat(self, model: str, messages: List[Dict], timeout: int = 60):
        # Uses Ollama stream or simple chat endpoint. Here we use non-streaming /chat for simplicity.
        url = f"{self.base}/api/chat"
        payload = {"model": model, "messages": messages}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            return r.json()

class LLMProvider:
    def __init__(self, cfg=None):
        self.client = OllamaClient()
        self.rag = RAGPipeline()

    async def process_pipeline(self, audio: Optional[bytes] = None, text: Optional[str] = None, opts: dict = None) -> str:
        opts = opts or {}
        # 1) STT via Ollama (if audio)
        if audio:
            # send audio to Ollama whisper model — model naming can vary
            # here we send base64 or appropriate payload depending on your Ollama setup
            resp = await self.client.chat("whisper", [{"role":"user","content":"<audio_payload_placeholder>"}])
            text = resp["message"]["content"]

        if not text:
            raise ValueError("No text provided")

        # 2) Summarize with Llama3.2 (optional)
        if not opts.get("skip_summarizer"):
            resp = await self.client.chat("llama-3.2", [{"role":"user", "content": f"Summarize: {text}"}])
            summary = resp["message"]["content"]
        else:
            summary = text

        # 3) RAG retrieval (Pinecone)
        docs = []
        if not opts.get("skip_rag"):
            docs = await self.rag.retrieve(summary, top_k=5)

        # 4) Final MedGemma answer - include docs in prompt
        prompt = summary
        if docs:
            ctx = "\n\n".join([d["text"] for d in docs])
            prompt = f"Context:\n{ctx}\n\nUser: {summary}"

        final_resp = await self.client.chat("medgemma-4b-it", [{"role":"user", "content": prompt}])
        final_text = final_resp["message"]["content"]
        return final_text
```
Notes: adjust chat endpoint payload per your Ollama API (streaming vs non-streaming). If you want token streaming, call Ollama streaming endpoints and forward chunks via WebSocket from chat_manager.

**Example-(`app/services/rag/pipeline.py`)** 
**RAG (LangChain + Pinecone sketch)**
```python
from typing import List, Dict, Optional
import os
# Use pinecone client + langchain if desired. This is a simple wrapper prototype.
import pinecone
from app.core.config import PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(PINECONE_INDEX)

class RAGPipeline:
    def __init__(self, index=None):
        self.index = index or index

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Sync pinecone client is used here; if you need async, run in threadpool.
        Returns list of {'id':..., 'text':..., 'score': ...}
        """
        # simple vectorization step needed (e.g., use an embedding model). Here we assume you have a function embed(query).
        # Replace `embed` with your embedding call (OpenAI, Ollama embedding, or local).
        embedding = await self._embed_text(query)
        res = self.index.query(vector=embedding, top_k=top_k, include_metadata=True)
        docs = []
        for match in res["matches"]:
            docs.append({"id": match["id"], "text": match["metadata"].get("text", ""), "score": match["score"]})
        return docs

    async def _embed_text(self, text: str):
        # Implement embedding call — can be Ollama embeddings or another provider.
        # Placeholder: return a zero-vector or call an embedding model.
        return [0.0] * 1536
```
Notes: Pinecone's Python client is synchronous; you can call it inside run_in_executor if you want async behavior. For production, use a proper embedder and store text in metadata.

**Example-(`app/services/chat_manager.py`)**
```python
from .llm_provider import LLMProvider
from sqlalchemy.ext.asyncio import AsyncSession

class ChatManager:
    def __init__(self, db: AsyncSession, provider: LLMProvider = None):
        self.db = db
        self.provider = provider or LLMProvider()

    async def handle_user_message(self, conversation_id, user_id, text=None, audio=None, ws_streamer=None):
        # Persist user message (implement create_message in your CRUD)
        # await create_message(conversation_id, "user", text, self.db)

        # Call pipeline
        final_answer = await self.provider.process_pipeline(audio=audio, text=text)

        # Send streaming chunks via ws_streamer
        if ws_streamer:
            chunk_size = 256
            for i in range(0, len(final_answer), chunk_size):
                await ws_streamer.send_chunk(conversation_id, final_answer[i:i+chunk_size])
            await ws_streamer.send_done(conversation_id, final_answer)

        # Persist assistant message
        # await create_message(conversation_id, "assistant", final_answer, self.db)
        return final_answer
```

**Tests**
- Add a test file backend/app/tests/test_pipeline.py with mock provider or set env USE_DEV_LLM=true so LLMProvider returns canned responses. Test that:
   - ChatManager.handle_user_message returns final text,
   - For WS: mock ws_streamer receives send_chunk and send_done calls.

**Acceptance**
- Given audio , image or text input, back-end runs: STT (Ollama/Whisper) → summarizer (Ollama/Llama3.2) → RAG retrieval (Pinecone) → final answer (Ollama/MedGemma).  
- Final response is streamed to frontend via `chunk`/`done` and saved to DB.  
- All model choices/config are toggled from `core/config.py` (no hard-coded model names).
- Dev-mode: pipeline returns canned response and saved to DB. 
- Audio flow: simulate audio payload -> pipeline returns transcription-based answer.
- RAG flow: seed Pinecone test index and verify docs influence final prompt (can inspect logs).


#### B08 — Moderation & Safety

**Actions**

- Simple keyword moderation on input/output; configurable via ENABLE_MODERATION
- Emergency keywords trigger flag in message metadata and in UI for critical keywords
- Admin log for flagged events (to console or collection)

**Rules & Severity Mapping**
- Implement keyword-based screening for offensive, violent, or medical-risk content.
- Maintain a JSON rules file `app/core/moderation_rules.json`:
  ```json
  {
    "high": ["suicide", "self harm", "violence", "kill myself", "bomb"],
    "medium": ["drug", "prescription", "sex", "blood", "weapon"],
    "low": ["stupid", "idiot", "hate"]
  }
  ```
- In moderation.py:
  - For each incoming user message, scan text (case-insensitive).
  - If any high severity match → block message, log to admin metrics, return {error: "unsafe"}.
  - If medium → allow but mark flagged=true in DB.
  - If low → allow and log warning.
  - Log violations in app/logs/moderation.log.
  - Extend later with AI moderation model if available.

**Acceptance**

- Blocked content returns safe message; flags recorded
- Admin logs show flagged items

#### B09 — Admin & Observability

**Actions**

- /api/admin/stats (role protected): totals, daily conversations, token counts
- Structured JSON logs
- Optional /metrics (feature-flagged) for Prometheus

**Logging & Metrics Implementation**
- Use `loguru` for structured logs; configure rotation and retention.
  ```python
  from loguru import logger
  logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")
  ```
- Define separate log files:
  - logs/app.log (info, warnings)
  - logs/error.log (errors/exceptions)
  - logs/moderation.log (from moderation module)

- Add /api/admin/metrics endpoint returning:
```json
{
  "uptime": "...",
  "active_conversations": 5,
  "messages_today": 120,
  "flagged_messages": 3
}
```
- For metrics collection, integrate prometheus-fastapi-instrumentator:
```bash
  pip install prometheus-fastapi-instrumentator
```
and expose /metrics.

- Add ENABLE_METRICS flag in .env (default false).

**Acceptance**

- Admin Stats reflect seed data; logs are structured and searchable.
- Logs rotate correctly and old files deleted after 7 days.
- /api/admin/metrics returns real-time stats.
- When ENABLE_METRICS=true, Prometheus endpoint accessible.


#### B010 — Backend Tests

**Actions**

- pytest + httpx/pytest-asyncio for auth, CRUD, WebSocket simulation

**Test Matrix & Fixtures**
- Frameworks: `pytest`, `pytest-asyncio`, `httpx`
- Fixtures:
  - `db_session`: yields isolated async test DB (SQLite in-memory or Postgres test DB)
  - `client`: FastAPI `AsyncClient` for API tests
  - `mock_llm_provider`: returns canned responses (no Ollama call)
  - `tmp_upload_dir`: temp folder for file upload tests
- Test categories:
  1. **Unit** — core/utils, moderation, auth hash
  2. **Integration** — DB CRUD, API endpoints, WebSocket streaming
  3. **Pipeline** — llm_provider mock pipeline returns valid text
  4. **Upload** — image/audio uploads stored and retrievable
  5. **Moderation** — block & flag scenarios
- Run matrix (CI):
  - Python 3.10 & 3.11
  - PostgreSQL latest
- Commands:
  ```bash
  pytest -v --asyncio-mode=auto
  coverage run -m pytest && coverage report
  ```

**Acceptance**

- pytest green locally.
- All tests pass locally and in CI.
- Coverage ≥ 80%.

```md
**Backend PostgreSQL Migration Checklist**

- [ ] Replace Beanie/Motor deps with SQLAlchemy[asyncio] + asyncpg + Alembic.
- [ ] Implement db.py (engine/session), models.py (ORM), config.py (env loader).
- [ ] Update CRUD/auth to use SQLAlchemy sessions.
- [ ] Configure Alembic for migrations.
- [ ] Verify docker-compose includes postgres service and DATABASE_URL.

**Developer note (integration)**

- Frontend sends user input (text or audio) to messages POST or WebSocket. `api/routers/messages.py` or ws route should call `ChatManager.handle_user_message(...)`.
- `chat_manager` must call `llm_provider.process_pipeline(...)` to centralize model orchestration.
- RAG retrieval (Pinecone) is done inside `services/rag/pipeline.py` and its output is passed to the final model prompt.
- For unit tests, use dev-mode (canned responses) inside `llm_provider`.
```


### Phase I — Integration & Advanced Features

#### I00 — Wire Frontend to Real API

**Actions**

- Set VITE_USE_MOCK_API=false
- services/api.js: Axios baseURL = VITE_API_BASE, interceptors add access token & handle 401 with refresh
- chatService.js: point to real endpoints

**Acceptance**

- Login/Register/Refresh works against backend; /chat loads real conversations/messages.

#### I01 — Real Streaming

**Actions**

- useWebSocket.js: connect to VITE_WS_BASE/ws/conversations/{id}?token=<JWT>
- Replace mock stream with server stream; keep reconnect/backoff

**Acceptance**

- Live token streaming visible; partial → final transition correct; reconnect idempotent.

#### I01.5 — Real Streaming, Reconnect & Media Pipeline Details

**Streaming Reconnect Protocol**
- Client maintains exponential backoff retry: 1s → 2s → 4s → 8s (max 30s).
- On reconnect, client sends:
  ```json
  { "type": "resume", "conversationId": "<id>", "lastMessageId": "<last_id>" }
  ```
- Server verifies JWT again and resumes the stream from last sent chunk if cached,
otherwise acknowledges with { "type": "resume_ack" } and continues normal flow.
  
**Server Implementation**
- Keep short-term stream cache (e.g., Redis or in-memory dict) keyed by conversation_id
storing last message text and status.
- If reconnect occurs within 30 seconds, reuse cached content and continue streaming.

**Voice / Audio Handling Pipeline**
- Accept audio (audio/mpeg or audio/wav) via /api/conversations/{id}/messages (multipart/form-data).
- Transcode audio to 16 kHz mono WAV before STT to ensure model compatibility.
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```
- Implement app/services/media_utils.py:
```python
    import subprocess
    async def transcode_audio(src_path, dst_path):
        cmd = ["ffmpeg", "-i", src_path, "-ar", "16000", "-ac", "1", dst_path]
        subprocess.run(cmd, check=True)
```    
- llm_provider.process_pipeline() uses the transcoded file path for Wispr/Whisper transcription.

**Clarification**
- Audio files are uploaded temporarily for transcription (voice input → text) using Wispr/Whisper.
- Audio messages are **not** stored permanently or replayable — only transcribed, then deleted.
- After transcription, delete the temporary audio file to save storage.
- In production, transient files can be auto-cleaned with a background job (e.g., delete after 5 minutes).
- Default MIME: audio/wav; maximum size 8 MB (configurable).

**Acceptance**

- If network drops, chat auto-reconnects and resumes within 30 s.
- Audio uploads are transcoded locally and processed by STT without errors.

#### I02 — Image Upload & Voice Input

**Actions**

- Image: ImageUploader → backend upload endpoint; store metadata; render as message
- Voice: capture audio (Web Speech API or MediaRecorder), send for transcription  (Whisper/Wispr), append text message
- Ensure disclaimer footer appears on all assistant messages

**Image upload API (spec)**
- POST /api/conversations/{id}/messages (multipart/form-data):
  - Fields:
    - `type`: `"image"` (or `"audio"` for voice input)
    - `file`: the uploaded image/audio
    - `metadata`: optional JSON (e.g., `{ "width": ..., "height": ... }`)
  - Accept: `image/png`, `image/jpeg`, `image/webp`, `audio/mpeg`, `audio/wav`.
  - Max: 8MB (configurable)
- Storage:
  - Store all image uploads in a local directory, i.e, Dev: store in `./uploads/` and save path in DB
  - Store files under ./uploads/{conversation_id}/{timestamp}_{filename}
  - Mount static route in FastAPI:
  ```python
  app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
  ```
  - Backend returns JSON: 
  ```json
  {"url": "/uploads/<conversation_id>/<filename>", "type": "image" | "audio" }
  ```
  - In DB: store message with type=image (or type=audio if used) and metadata {url, mime_type, size}

- Later(Prod): upload to S3 (presigned URL pattern). Add S3 env vars: S3_BUCKET, S3_REGION, S3_KEY, S3_SECRET

**Acceptance**

- File URL loads via static route /uploads/*.
- Image messages persist; voice → text → message displayed.
- Voice capture converts to text and sends as a user message

#### I03 — Moderation UI & Emergency Modal

**Actions**

- When backend flags severe symptoms, show modal with emergency resources
- Blocked content feedback in Composer

**Acceptance**

- Triggering keywords displays modal; UX remains non-blocking.


### Phase D — Docker, CI, Docs

#### D00 — Dockerfiles & Compose

**Actions**

- docker/frontend.Dockerfile (Node 20, npm run dev -- --host)
**Frontend Dockerfile (Frontend/Dockerfile)**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "run", "preview", "--", "--host"]
```

- docker/backend.Dockerfile (Python 3.11, uvicorn reload)
**Backend Dockerfile (backend/Dockerfile)**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
- docker-compose.yml for frontend, backend, postgres (image: postgres:16) , Add volume postgres_data.
**Compose Services Update**
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./uploads:/app/uploads
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: veda
    ports: ["5432:5432"]
  adminer:
    image: adminer
    ports: ["8080:8080"]
```
**Commands(PowerShell)**

```powershell
cd .\veda
copy .env.example .env
docker-compose up --build
```

**Acceptance**
- docker compose up brings all services online and frontend connects to backend.
- Visiting http://localhost:5173 → login → chat with streaming works end-to-end.

#### D01 — README & Dev Onboarding

**Actions**

- Expand `.env.example`
- Add README with run instructions, architecture diagram, API endpoints summary, seed data notes

**Acceptance**

- A new dev can clone → `docker-compose up` → use app in <10 minutes.

#### D02 — CI (GitHub Actions)

**Actions**

- Frontend: install → lint → test
- Backend: install → pytest
- Cache node/pip

**CI (GitHub Actions) — minimal workflow**
- Add `.github/workflows/ci.yml`:
  - Steps: checkout, setup-node, setup-python, install deps, run linters, run `alembic upgrade head` on test db, run backend pytest, run frontend npm test.
- Ensure secrets (DB, Pinecone) are stored in GitHub Secrets and test DB is created via Docker services in workflow.

**GitHub Actions CI Workflow**

_File: `.github/workflows/ci.yml`_
```yaml
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  build-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: veda_test
        ports: [5432:5432]
        options: >-
          --health-cmd="pg_isready -U postgres"
          --health-interval=5s --health-timeout=5s --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - name: Install backend deps
        run: pip install -r backend/requirements.txt
      - name: Install frontend deps
        run: cd frontend && npm ci
      - name: Run Alembic migrations
        run: cd backend && alembic upgrade head
      - name: Run backend tests
        run: cd backend && pytest -v --asyncio-mode=auto
      - name: Run frontend tests
        run: cd frontend && npm test -- --watchAll=false
```
**Acceptance**

- CI green on PR; min coverage threshold (e.g., 70%).
- CI runs on every PR, builds both apps, migrates DB, and passes tests on main.

## 4. API Contracts (freeze before backend work)

**Auth**

- POST /api/auth/register → {email, password, name} → 201 user
- POST /api/auth/login → {email, password} → {access, refresh}
- POST /api/auth/refresh → {refresh} → {access}
- GET /api/auth/me → header Bearer → user
- Google: /api/auth/google/login (redirect), /api/auth/google/callback

**Conversations**

- GET /api/conversations → list
- POST /api/conversations → {title?} → {id}
- GET /api/conversations/{id} → conversation
- DELETE /api/conversations/{id} → 204

**Messages**

- GET /api/conversations/{id}/messages → list
- POST /api/conversations/{id}/messages → {content, type=text|image|voice, metadata?} → {id}

**Stream**

- GET ws:/ws/conversations/{id}?token=<JWT>
- Events: chunk | done | error (see payloads above)

---

## Keep these in docs/api-contract.md and import shapes in frontend/src/services/contracts.js (JS objects) to align UI and server.

## 5. Security & Safety

- Store access token in memory;store refresh token in localStorage (or secure cookie if later adopted)
- Strict CORS: allow only http://localhost:5173 in dev
- Validate uploads (size/type) for images; sanitize any rendered HTML
- Server appends disclaimer to assistant messages

**Cookie & HTTPS Recommendations (for prod)**
- For web clients, prefer `HttpOnly` cookies for refresh tokens to prevent XSS leaks.
- Access token stays in memory only (never `localStorage`).
- Enable `Secure` and `SameSite=Strict` attributes on cookies in production.
- Enforce HTTPS by default:
  - Redirect HTTP → HTTPS using a middleware (e.g., `starlette.middleware.httpsredirect.HTTPSRedirectMiddleware`).
  - Set `SECURE_PROXY_SSL_HEADER=("x-forwarded-proto","https")` in reverse proxy.
- Add CORS policy:
  ```python
  origins = ["http://localhost:5173", "https://veda.app"]
  app.add_middleware(CORSMiddleware,
      allow_origins=origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"])
  ```
- Use Helmet-like headers for extra security:
  ```python
  from starlette.middleware.trustedhost import TrustedHostMiddleware
  app.add_middleware(TrustedHostMiddleware, allowed_hosts=["veda.app","localhost"])
  ```
**Acceptance**
 - All HTTP endpoints redirect to HTTPS in prod.
 - Refresh tokens stored securely as HttpOnly cookies.
 - CORS and host policies prevent unauthorized origins.

## 6. Developer Runbook

### One-time

**Commands(PowerShell)**

```powershell
cd .\veda
copy .env.example .env
```

### Local (without Docker)

**Commands(PowerShell)**

```powershell
# Backend
cd .\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd .\frontend
npm install
npm run dev
```

### Local (with Docker)

**Commands(PowerShell)**

```powershell
cd .\veda
docker-compose up --build
```

## 7. Risks & Mitigations

- Google OAuth setup complexity → document console steps, provide fallback email/password flow
- WebSocket auth and reconnect edge cases → implement exponential backoff and idempotent message persistence
- Streaming backpressure → throttle, batch partial DB writes
- Large image/voice payloads → enforce limits; offload heavy work
- Index performance → ensure indexes on startup; monitor slow queries

## 8. Definition of Done (per feature)

- Code + tests + docs updated
- Lint passes; unit tests green; CI green
- Manual acceptance meets criteria in this plan

## 9. Deliverables Checklist

- [ ] Frontend UI complete with mocks (REST + WS)
- [ ] Backend auth (JWT + Google) end‑to‑end
- [ ] CRUD for conversations/messages
- [ ] Streaming chat with disclaimer
- [ ] Integration (real API + WS)
- [ ] Image upload + voice input
- [ ] Moderation + emergency modal
- [ ] Admin stats + logs
- [ ] Dockerized dev environment with frontend/backend/MongoDB
- [ ] Tests (FE+BE) + CI
- [ ] README + .env.example + API contracts

## 10. Timeline (rough)

- Weeks 1–2: Phase F (F00–F09) + B00–B05 core
- Week 3: B06–B08, Integration (I00–I03), Docker/CI/Docs (D00–D02)
