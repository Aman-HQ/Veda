"""
Veda Chatbot - FastAPI Backend
Main application entry point with health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

# Create FastAPI app instance
app = FastAPI(
    title="Veda Chatbot API",
    description="Healthcare chatbot API with streaming support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
# Allow localhost for development
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    
    Returns:
        dict: Status information including timestamp and service status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "veda-backend",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
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
    Future: Initialize database connections, load models, etc.
    """
    print("🚀 Veda Backend starting up...")
    print(f"📝 Documentation available at: /docs")
    print(f"❤️  Health check available at: /health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down.
    Future: Close database connections, cleanup resources, etc.
    """
    print("👋 Veda Backend shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
