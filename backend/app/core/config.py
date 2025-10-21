"""
Configuration module for Veda backend.
Loads environment variables and provides centralized config access.
"""
import os
from typing import Optional

# -------------------------------
# Database Configuration
# -------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/veda"
)

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "veda")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# -------------------------------
# Authentication & Security
# -------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "replace_me_with_secure_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# -------------------------------
# Google OAuth Configuration
# -------------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI", 
    "http://localhost:5173/oauth/callback"
)

# -------------------------------
# Ollama Configuration
# -------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

# -------------------------------
# Pinecone Configuration
# -------------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "veda-index")

# -------------------------------
# LLM / AI Provider Configuration
# -------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://llm:8080")
ENABLE_MODERATION = os.getenv("ENABLE_MODERATION", "true").lower() == "true"
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "false").lower() == "true"

# -------------------------------
# CORS Configuration
# -------------------------------
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000"
).split(",")

# -------------------------------
# Application Settings
# -------------------------------
APP_NAME = "Veda Healthcare Chatbot"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

