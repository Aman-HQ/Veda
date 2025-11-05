import firebase_admin
from firebase_admin import credentials, auth
from app.core import config
import os
import logging

logger = logging.getLogger(__name__)

try:
    # Initialize Firebase Admin SDK using config module
    cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    logger.info("✅ Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"❌ Firebase initialization failed: {str(e)}")
    raise

def get_firebase_auth():
    """Returns Firebase Auth instance"""
    return auth