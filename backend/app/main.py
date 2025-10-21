"""
Veda Chatbot - FastAPI Backend
Main application entry point with health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlalchemy import text
from app.core import config
from app.db.session import engine
from app.db.init_db import init_db

# Create FastAPI app instance
app = FastAPI(
    title=config.APP_NAME,
    description="Healthcare chatbot API with streaming support",
    version=config.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration using config module
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    Tests database connectivity as part of health check.
    
    Returns:
        dict: Status information including timestamp and service status
    """
    db_status = "unknown"
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "veda-backend",
            "timestamp": datetime.utcnow().isoformat(),
            "version": config.APP_VERSION,
            "database": db_status
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
        "health": "/health"
    }


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
