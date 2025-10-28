"""
Veda Chatbot - FastAPI Backend
Main application entry point with health check endpoint.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import config
from app.db.session import engine, get_db
from app.db.init_db import init_db
from app.api.routers import auth_router, conversations_router, messages_router
from app.api.routers.stream import router as stream_router, start_cleanup_task
from app.api.routers.admin import router as admin_router
from app.api.routers.uploads import router as uploads_router
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.logging_config import setup_logging, log_system_event
import traceback
import time
import logging

# Import Prometheus instrumentation (conditionally based on config)
if config.ENABLE_METRICS:
    from prometheus_fastapi_instrumentator import Instrumentator

# Initialize structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Track application start time for uptime metrics
app_start_time = datetime.utcnow()

# Create FastAPI app instance
app = FastAPI(
    title=config.APP_NAME,
    description="Healthcare chatbot API with streaming support",
    version=config.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request timing and logging middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request timing and logging middleware."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response


# CORS configuration using config module
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    if config.DEBUG:
        # In debug mode, return detailed error information
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "traceback": traceback.format_exc().split('\n')
            }
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages_router, prefix="/api", tags=["messages"])
app.include_router(stream_router, tags=["websocket"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(uploads_router, prefix="/api", tags=["uploads"])

# Conditionally instrument Prometheus metrics
if config.ENABLE_METRICS:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,  # Use our config instead of environment variable
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Instrument the app
    instrumentator.instrument(app)
    
    # Expose metrics endpoint
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=True, tags=["monitoring"])
    
    logger.info("✓ Prometheus metrics enabled at /metrics")


@app.get("/health")
async def health_check():
    """
    Enhanced health check endpoint to verify the service is running.
    Tests database connectivity and provides detailed system information.
    
    Returns:
        dict: Status information including timestamp, service status, and database info
    """
    db_status = "unknown"
    db_info = {}
    
    try:
        # Test database connection and get info
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            
            # Get database version and connection info
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # Count tables
            tables_result = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            table_count = tables_result.scalar()
            
        db_status = "connected"
        db_info = {
            "version": version.split(',')[0] if version else "unknown",
            "host": config.POSTGRES_HOST,
            "database": config.POSTGRES_DB,
            "tables": table_count
        }
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_info = {"error": str(e)}
    
    return JSONResponse(
        status_code=200 if db_status == "connected" else 503,
        content={
            "status": "healthy" if db_status == "connected" else "unhealthy",
            "service": "veda-backend",
            "timestamp": datetime.utcnow().isoformat(),
            "version": config.APP_VERSION,
            "database": {
                "status": db_status,
                **db_info
            },
            "environment": {
                "debug": config.DEBUG,
                "cors_origins": config.CORS_ORIGINS
            }
        }
    )


@app.get("/")
async def root():
    """
    Root endpoint with basic API information.
    
    Returns:
        dict: Welcome message and API documentation link
    """
    return {
        "message": "Welcome to Veda Chatbot API",
        "docs": "/docs",
        "health": "/health",
        "version": config.APP_VERSION
    }


@app.post("/chat")
async def demo_chat(username: str, user_message: str, db: AsyncSession = Depends(get_db)):
    """
    Demo chat endpoint showing FastAPI-SQLAlchemy integration.
    This is a simplified example as shown in the plan.
    
    Args:
        username: User identifier (email)
        user_message: Message content from user
        db: Database session
        
    Returns:
        dict: Response with generated message
    """
    try:
        async with db.begin():
            result = await db.execute(select(User).where(User.email == username))
            user = result.scalars().first()

            if not user:
                # Create user if doesn't exist (for demo purposes)
                user = User(email=username, name=username.split('@')[0] if '@' in username else username)
                db.add(user)
                await db.refresh(user)

            # Create or reuse a default conversation
            result = await db.execute(
                select(Conversation).where(
                    Conversation.user_id == user.id,
                    Conversation.title == "Demo Chat"
                )
            )
            conv = result.scalars().first()
            
            if not conv:
                conv = Conversation(user_id=user.id, title="Demo Chat")
                db.add(conv)
                await db.refresh(conv)

            # Add user message
            user_msg = Message(
                conversation_id=conv.id, 
                sender="user", 
                content=user_message,
                message_metadata={"demo": True}
            )
            db.add(user_msg)
            await db.refresh(user_msg)

            # Generate response (placeholder for LLM integration)
            response_content = f"Thank you for your message: '{user_message}'. This is a demo response from Veda Healthcare Assistant."
            
            # Add healthcare disclaimer
            disclaimer = "\n\n⚠️ This is for informational purposes only and should not replace professional medical advice."
            response_content += disclaimer

            # Save assistant response
            bot_msg = Message(
                conversation_id=conv.id, 
                sender="assistant", 
                content=response_content,
                message_metadata={"demo": True, "disclaimer": True}
            )
            db.add(bot_msg)
            
            # Update conversation message count
            # conv.messages_count = conv.messages_count + 2  # user + assistant
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conv.id)
                .values(messages_count=Conversation.messages_count + 2)
            )
            await db.refresh(bot_msg)
        # Transaction commits here automatically

        return {
            "response": response_content,
            "conversation_id": str(conv.id),
            "message_id": str(bot_msg.id),
            "user": user.name,
            "demo": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing error: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts.
    Initializes database connections and verifies connectivity.
    """
    print("🚀 Veda Backend starting up...")
    print(f"📝 Documentation available at: /docs")
    print(f"❤️  Health check available at: /health")
    
    # Test database connection
    try:
        print("🔌 Testing database connection...")
        async with engine.begin() as conn:
            # Simple connectivity test
            await conn.execute(text("SELECT 1"))
        print(f"✓ Database connected successfully: {config.POSTGRES_DB}@{config.POSTGRES_HOST}")
        
        # Initialize database tables (for development)
        # In production, use Alembic migrations instead
        if config.DEBUG:
            print("🔧 Initializing database tables...")
            await init_db()
        
        # Start background cleanup task for WebSocket stream cache
        print("🧹 Starting background cleanup task...")
        start_cleanup_task()
        
        # Log system startup
        log_system_event("application_startup", "main", {"version": "1.0.0", "debug": config.DEBUG})
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("⚠️  Application will start but database operations will fail")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down.
    Closes database connections and cleanup resources.
    """
    print("👋 Veda Backend shutting down...")
    
    # Close database connections
    try:
        await engine.dispose()
        print("✓ Database connections closed")
    except Exception as e:
        print(f"⚠️  Error closing database: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
