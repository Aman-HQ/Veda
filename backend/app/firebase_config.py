import firebase_admin
from firebase_admin import credentials, auth
from decouple import config
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate(config('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred)

def get_firebase_auth():
    """Returns Firebase Auth instance"""
    return auth