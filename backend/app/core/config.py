"""
Configuration module for Veda backend.
Loads environment variables and provides centralized config access.
"""
import os
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# Load .env file automatically
load_dotenv(find_dotenv())

# -------------------------------
# Database Configuration
# -------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:your_password@localhost:5432/veda"
)

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "veda")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# -------------------------------
# Authentication & Security
# -------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "secret_key")
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
# Audio Provider Configuration (Ollama vs Bhashini)
# -------------------------------
AUDIO_PROVIDER = os.getenv("AUDIO_PROVIDER", "bhashini")  # "ollama" or "bhashini"
BHASHINI_BASE_URL = os.getenv("BHASHINI_BASE_URL", "https://bhashini.gov.in/api/v1")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")

# -------------------------------
# RAG & Document Processing Configuration
# -------------------------------
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./data/documents")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "llama-text-embed-v2")

# -------------------------------
# Model Configuration
# -------------------------------
STT_MODEL = os.getenv("STT_MODEL", "whisper")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "llama3.2")
MAIN_MODEL = os.getenv("MAIN_MODEL", "medgemma-4b-it")
TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "mistral")

# -------------------------------
# Pipeline Control Flags
# -------------------------------
SKIP_SUMMARIZER = os.getenv("SKIP_SUMMARIZER", "false").lower() == "true"
SKIP_RAG = os.getenv("SKIP_RAG", "false").lower() == "true"
USE_DEV_LLM = os.getenv("USE_DEV_LLM", "true").lower() == "true"

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
# Firebase Configuration
# -------------------------------
FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH",
    "./firebase-credentials.json"
)

# -------------------------------
# Redis Configuration
# -------------------------------
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_STREAM_CACHE_TTL = int(os.getenv("REDIS_STREAM_CACHE_TTL", "30"))
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))
REDIS_RATE_LIMIT_TTL = int(os.getenv("REDIS_RATE_LIMIT_TTL", "60"))
REDIS_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("REDIS_RATE_LIMIT_MAX_REQUESTS", "100"))

# -------------------------------
# Application Settings
# -------------------------------
APP_NAME = "Veda Healthcare Chatbot"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# -------------------------------
# File Upload Configuration
# -------------------------------
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))

