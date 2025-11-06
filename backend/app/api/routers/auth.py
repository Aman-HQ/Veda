"""
Authentication endpoints for user registration, login, and token management.
"""
from datetime import timedelta, datetime, timezone
from typing import Dict, Any
from uuid import UUID, uuid4
import requests
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from firebase_admin import auth as firebase_auth

from ...db.session import get_db
from ...crud.user import UserCRUD
from ...core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_token
)
from ...core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI
)
from ...schemas.auth import (
    UserCreate, 
    User, 
    Token, 
    LoginRequest, 
    RefreshTokenRequest,
    GoogleOAuthRequest,
    PasswordResetRequest,
    SyncPasswordRequest
)
from ...api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    Creates user in both PostgreSQL and Firebase, then sends email verification.
    
    Args:
        user_create: User registration data
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email already exists
        
    Note:
        This endpoint is for email/password users only. 
        Google Sign-In users follow a different flow and don't need email verification.
    """
    email = user_create.email.lower().strip()
    
    # Check if user already exists
    existing_user = await UserCRUD.get_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user in PostgreSQL
    try:
        user = await UserCRUD.create(db, user_create)
        
        # Step 2: Create user in Firebase with email_verified=False
        try:
            firebase_user = firebase_auth.create_user(
                email=email,
                email_verified=False  # Not verified yet
            )
            logger.info(f"Created Firebase user for email verification: {email}")
        except firebase_auth.EmailAlreadyExistsError:
            logger.warning(f"Firebase user already exists for: {email}")
            # Continue anyway, we'll send verification email
        
        # Step 3: Get Firebase custom token and send verification email
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if FIREBASE_WEB_API_KEY:
            try:
                logger.info(f"Sending verification email via Firebase REST API...")
                
                # Step 3a: Create custom token for the Firebase user
                custom_token = firebase_auth.create_custom_token(firebase_user.uid)
                
                # Step 3b: Exchange custom token for ID token
                token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
                token_response = requests.post(token_url, json={
                    "token": custom_token.decode('utf-8'),
                    "returnSecureToken": True
                })
                
                if token_response.status_code != 200:
                    logger.error(f"❌ Failed to get ID token: {token_response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to initialize email verification"
                    )
                
                id_token = token_response.json().get('idToken')
                
                # Step 3c: Send verification email using ID token
                verification_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                verification_payload = {
                    "requestType": "VERIFY_EMAIL",
                    "idToken": id_token
                }

                verification_response = requests.post(verification_url, json=verification_payload)

                if verification_response.status_code == 200:
                    logger.info(f"✅ Verification email sent successfully to {email}")
                else:
                    logger.error(f"❌ Firebase email sending failed: {verification_response.status_code}")
                    logger.error(f"Response: {verification_response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to send verification email. Please try resending it."
                    )
            except Exception as e:
                logger.error(f"Error sending verification email: {str(e)}")
                # Don't fail registration, but inform user
                logger.warning("User created but verification email failed")
        else:
            logger.warning("Firebase Web API Key not configured - skipping verification email")
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get access and refresh tokens.
    
    Email verification is REQUIRED for users who signed up with email/password.
    Google OAuth users bypass email verification since Google already verifies emails.
    
    Args:
        login_request: Login credentials
        request: HTTP request for extracting user agent
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid or email is not verified
    """
    # Authenticate user
    user = await UserCRUD.authenticate(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check email verification for email/password users only
    # Skip verification check for Google OAuth users
    if user.auth_provider == 'email':
        try:
            # Check Firebase email verification status
            firebase_user = firebase_auth.get_user_by_email(user.email)
            
            if not firebase_user.email_verified:
                logger.warning(f"Login attempt with unverified email: {user.email}")
                
                # Resend verification email with ID token
                FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
                
                if FIREBASE_WEB_API_KEY:
                    try:
                        # Get custom token and exchange for ID token
                        custom_token = firebase_auth.create_custom_token(firebase_user.uid)
                        token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
                        token_response = requests.post(token_url, json={
                            "token": custom_token.decode('utf-8'),
                            "returnSecureToken": True
                        })
                        
                        if token_response.status_code == 200:
                            id_token = token_response.json().get('idToken')
                            
                            # Send verification email
                            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                            payload = {
                                "requestType": "VERIFY_EMAIL",
                                "idToken": id_token
                            }
                            
                            response = requests.post(url, json=payload)
                            
                            if response.status_code == 200:
                                logger.info(f"Verification email resent to {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to resend verification email: {str(e)}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified. A new verification email has been sent."
                )
                
        except firebase_auth.UserNotFoundError:
            # Create Firebase user if doesn't exist (legacy users)
            try:
                firebase_user = firebase_auth.create_user(
                    email=user.email,
                    email_verified=False
                )
                logger.info(f"Created Firebase user for legacy account: {user.email}")
                
                # Send verification email with ID token
                FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
                
                if FIREBASE_WEB_API_KEY:
                    try:
                        # Get custom token and exchange for ID token
                        custom_token = firebase_auth.create_custom_token(firebase_user.uid)
                        token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
                        token_response = requests.post(token_url, json={
                            "token": custom_token.decode('utf-8'),
                            "returnSecureToken": True
                        })
                        
                        if token_response.status_code == 200:
                            id_token = token_response.json().get('idToken')
                            
                            # Send verification email
                            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                            payload = {
                                "requestType": "VERIFY_EMAIL",
                                "idToken": id_token
                            }
                            
                            response = requests.post(url, json=payload)
                            
                            if response.status_code == 200:
                                logger.info(f"Verification email sent to legacy user: {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to send verification email: {str(e)}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not verified. A verification email has been sent."
                )
            except Exception as e:
                logger.error(f"Failed to create Firebase user for legacy account: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred. Please contact support."
                )
    else:
        # Google OAuth user - skip verification check
        logger.info(f"Login by Google OAuth user (skipping email verification): {user.email}")
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_token_expires
    )
    
    # Store refresh token metadata (optional - for token management)
    refresh_tokens = user.refresh_tokens or []
    refresh_tokens.append({
        "token_id": str(uuid4()),  # Unique, non-correlatable identifier
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": request.headers.get("user-agent", "unknown") # Extract real user agent
    })
    
    # Keep only last 5 refresh tokens
    if len(refresh_tokens) > 5:
        refresh_tokens = refresh_tokens[-5:]
    
    await UserCRUD.update_refresh_tokens(db, user, refresh_tokens)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_request: Refresh token data
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify refresh token
    payload = verify_token(refresh_request.refresh_token, token_type="refresh")
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Get user from database
    user = await UserCRUD.get_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user data
    """
    return current_user


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth2 login flow.
    
    Returns:
        Redirect to Google OAuth2 authorization URL
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth2 not configured"
        )
    
    # Google OAuth2 authorization URL
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_OAUTH_REDIRECT_URI}"
        "&scope=openid email profile"
        "&response_type=code"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    return RedirectResponse(url=google_auth_url)


@router.post("/google/callback", response_model=Token)
async def google_callback(
    oauth_request: GoogleOAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth2 callback and create/login user.
    
    Args:
        oauth_request: OAuth2 authorization code
        request: HTTP request for extracting user agent
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If OAuth2 flow fails
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth2 not configured"
        )
    
    # Track if we created a new user (for rollback on error)
    user_created = False
    user = None

    try:
        logger.info(f"Processing Google OAuth callback with code: {oauth_request.code[:10]}...")
        
        # Exchange authorization code for access token
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": oauth_request.code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
                }
            )

            # Handle errors before parsing response
            if not token_response.is_success:
                try:
                    error_data = token_response.json()
                    error_code = error_data.get("error", "unknown")
                    error_description = error_data.get("error_description", "Unknown error")
                except Exception:
                    error_code = "unknown"
                    error_description = f"HTTP {token_response.status_code}"
                
                logger.error(f"Google OAuth token exchange failed - Status: {token_response.status_code}, Error: {error_code}, Description: {error_description}")
                
                # Handle specific error codes
                if error_code == "invalid_grant":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Authorization code has expired or already been used. Please try signing in again."
                    )
                elif token_response.status_code == 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid request: {error_description}"
                    )
                elif token_response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid client credentials. Please contact support."
                    )
                elif token_response.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied by Google. Please contact support."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google authentication failed. Please try again."
                    )
            
            token_data = token_response.json()
            logger.info("Google token exchange successful")

        # Get user info from Google
        async with httpx.AsyncClient(timeout=10.0) as client:
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_response.raise_for_status()
            google_user = user_response.json()

        user_email = google_user["email"]
        # user_name = google_user.get("name", "")
        logger.info(f"Google OAuth successful for user: {user_email}")
        
        # Check if user exists
        user = await UserCRUD.get_by_email(db, user_email)
        
        if not user:
            # Mark that we're creating a new user
            user_created = True
           
            # Create new user from Google data
            user = await UserCRUD.create_oauth_user(
                db,
                email=user_email,
                name=google_user.get("name", "")
            )
            logger.info(f"Created new OAuth user: {user_email}")
        else:
            # Existing user - check if we need to upgrade auth_provider
            if user.auth_provider == 'email':
                # ACCOUNT UPGRADE: User registered with email/password but now signing in via Google
                # Since Google has verified the email, we upgrade them to 'google' auth_provider
                logger.info(f"🔄 Upgrading user from 'email' to 'google' auth_provider: {user_email}")
                user = await UserCRUD.upgrade_to_oauth(db, user)
                logger.info(f"✅ User upgraded to Google OAuth: {user_email}")
            else:
                logger.info(f"Existing Google OAuth user logged in: {user_email}")

        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        # Store refresh token metadata with secure UUID identifier
        refresh_tokens = user.refresh_tokens or []
        refresh_tokens.append({
            "token_id": str(uuid4()),  # Unique identifier for this session
            "created_at": datetime.now(timezone.utc).isoformat(),   # When token was issued
            "user_agent": request.headers.get("user-agent", "unknown")  # Extract real user agent
        })
        
        # Keep only last 5 refresh tokens
        if len(refresh_tokens) > 5:
            refresh_tokens = refresh_tokens[-5:]
        
        await UserCRUD.update_refresh_tokens(db, user, refresh_tokens)

        # Commit the transaction
        await db.commit()
        
        logger.info(f"OAuth authentication completed successfully for {user_email}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        if user_created and user:
            await db.rollback()
            logger.warning(f"Rolled back user creation due to authentication error")
        raise
        
    except httpx.HTTPStatusError as e:
        logger.exception("Google OAuth2 HTTP error")

        # Rollback if user was created
        if user_created and user:
            await db.rollback()
            logger.warning(f"Rolled back user creation due to HTTP error")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to communicate with Google. Please try again."
        ) from e
    
    except (httpx.RequestError, httpx.TimeoutException) as e:
        logger.exception("Google OAuth2 network error")
        
        # Rollback if user was created
        if user_created and user:
            await db.rollback()
            logger.warning(f"Rolled back user creation due to network error")
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Google. Please try again."
        ) from e
    
    except (KeyError, ValueError) as e:
        logger.exception("OAuth2 data processing error")
    
        # Rollback if user was created
        if user_created and user:
            await db.rollback()
            logger.warning(f"Rolled back user creation due to data error")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth2 authentication failed. Please try again."
        ) from e


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle forgot password request.
    Generates Firebase password reset link and sends email.
    Uses Firebase REST API to trigger password reset email.

    Args:
        request: Password reset request with email
        db: Database session
        
    Returns:
        Generic success message (for security)
        
    Note:
        Always returns the same message regardless of whether the user exists,
        to prevent email enumeration attacks.
    """
    email = request.email.lower().strip()
    
    logger.info(f"========== FORGOT PASSWORD REQUEST ==========")
    logger.info(f"Email received: {email}")

    try:
        # Step 1: Check if user exists in PostgreSQL database
        user = await UserCRUD.get_by_email(db, email)
        
        # SECURITY: Always return same message regardless of whether user exists
        generic_message = "If an account exists for that email, a password reset link has been sent."
        
        if not user:
            logger.info(f"Password reset attempted for non-existent email: {email}")
            return {"message": generic_message}
        
        # Step 2: Check if user exists in Firebase (create if needed)
        logger.info(f"Checking if user exists in Firebase...")
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            logger.info(f"Firebase user found: {firebase_user.uid}")
        except firebase_auth.UserNotFoundError:
            logger.info(f"User not in Firebase, creating new user...")
            # Create user in Firebase with email_verified=True
            # They'll set their actual password via the reset link
            firebase_user = firebase_auth.create_user(
                email=email,
                email_verified=True  # Mark as verified since they're resetting password
            )
            logger.info(f"Created Firebase user for password reset: {email}")
        
        # Step 3: Send password reset email using Firebase REST API
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if not FIREBASE_WEB_API_KEY:
            logger.error("Firebase Web API Key not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service not configured"
            )

        logger.info(f"Sending password reset email via Firebase REST API...")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"

        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            logger.info(f"✅ Password reset email sent successfully to {email}")
            response_data = response.json()
            logger.info(f"Firebase response: {response_data}")
        else:
            logger.error(f"❌ Firebase email sending failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )

        logger.info(f"========== REQUEST COMPLETED SUCCESSFULLY ==========")

        # Firebase automatically sends the email!
        return {
            "message": generic_message,
            "success": True
        }
        
    except firebase_auth.FirebaseError as e:
        logger.error(f"Firebase error in forgot_password for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )
    except Exception as e:
        # logger.exception(f"Unexpected error in forgot_password for {email}")
        logger.error(f"========== ERROR IN FORGOT PASSWORD ==========")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )


@router.post("/sync-password")
async def sync_password_with_postgres(
    request: SyncPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync password to PostgreSQL after Firebase password reset.
    This endpoint is called AFTER the user resets their password via Firebase.
    
    Args:
        request: Firebase ID token and new password
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or password update fails
        
    Security:
        - Verifies Firebase ID token before updating password
        - Hashes password on backend (never store plain passwords)
        - Only updates password for authenticated Firebase users
    """
    try:
        # Step 1: Verify the Firebase ID token (security check)
        decoded_token = firebase_auth.verify_id_token(request.firebase_id_token)
        email = decoded_token.get('email')
        
        if not email:
            logger.error("No email found in Firebase token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: email not found"
            )
        
        logger.info(f"Verified Firebase token for password sync: {email}")
        
        # Step 2: Get user from PostgreSQL
        user = await UserCRUD.get_by_email(db, email)
        
        if not user:
            logger.error(f"User not found in PostgreSQL for password sync: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Step 3: Update password in PostgreSQL (will be hashed by UserCRUD)
        await UserCRUD.update_password(db, user, request.new_password)
        logger.info(f"Successfully updated password in PostgreSQL for: {email}")
        
        return {
            "message": "Password updated successfully",
            "success": True
        }
        
    except firebase_auth.InvalidIdTokenError as e:
        logger.error(f"Invalid Firebase token in sync_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )
    except firebase_auth.ExpiredIdTokenError as e:
        logger.error(f"Expired Firebase token in sync_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired. Please try resetting your password again."
        )
    except firebase_auth.RevokedIdTokenError as e:
        logger.error(f"Revoked Firebase token in sync_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has been revoked"
        )
    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in sync_password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating password. Please try again."
        )


@router.post("/resend-password-reset")
async def resend_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend password reset link.
    This endpoint allows users to request another password reset email
    if they didn't receive the first one or if the link expired.
    
    Args:
        request: Password reset request with email
        db: Database session
        
    Returns:
        Generic success message (for security)
        
    Note:
        Always returns the same message regardless of whether the user exists,
        to prevent email enumeration attacks. Identical logic to /forgot-password.
    """
    email = request.email.lower().strip()
    
    try:
        # Step 1: Check if user exists in PostgreSQL database
        user = await UserCRUD.get_by_email(db, email)
        
        # SECURITY: Always return same message regardless of whether user exists
        generic_message = "If an account exists for that email, a password reset link has been sent."
        
        if not user:
            logger.info(f"Password reset resend attempted for non-existent email: {email}")
            return {"message": generic_message}
        
        # Step 2: Check if user exists in Firebase (create if needed)
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            logger.info(f"Resending password reset for existing Firebase user: {email}")
        except firebase_auth.UserNotFoundError:
            # Create user in Firebase with email_verified=True
            # They'll set their actual password via the reset link
            firebase_user = firebase_auth.create_user(
                email=email,
                email_verified=True  # Mark as verified since they're resetting password
            )
            logger.info(f"Created Firebase user for password reset resend: {email}")
        
        # Send email via REST API
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if not FIREBASE_WEB_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service not configured"
            )

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            logger.info(f"✅ Resent password reset email to {email}")
        else:
            logger.error(f"❌ Failed to resend email: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )
        
        # Firebase automatically sends the email!
        return {
            "message": generic_message,
            "success": True
        }
        
    except firebase_auth.FirebaseError as e:
        logger.error(f"Firebase error in resend_password_reset for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error in resend_password_reset for {email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )


@router.post("/verify-email-and-login")
async def verify_email_and_login(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-login after email verification (simplified version).
    Called from frontend after applyActionCode marks email as verified.
    
    Args:
        request: Dictionary with email
        db: Database session
        
    Returns:
        access_token and refresh_token
        
    Raises:
        HTTPException: If email not verified or user not found

    Security:
        - Verifies email is marked as verified in Firebase
        - Only issues tokens for verified users
        - No need for Firebase ID token since email verification already happened client-side
    """
    try:
        email = request.get('email')
        
        if not email:
            logger.error("No email provided in verify-email-and-login request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        email = email.lower().strip()
        logger.info(f"Auto-login request for verified email: {email}")
        
        # Step 1: Check if email is verified in Firebase
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            
            if not firebase_user.email_verified:
                logger.warning(f"Email not verified in Firebase: {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not verified"
                )
            
            logger.info(f"✅ Email verified in Firebase: {email}")

        except firebase_auth.UserNotFoundError:
            logger.error(f"User not found in Firebase: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Firebase"
            )
        
        # Step 2: Get user from PostgreSQL
        user = await UserCRUD.get_by_email(db, email)
        
        if not user:
            logger.error(f"User not found in PostgreSQL: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"✅ User found in PostgreSQL: {email}")

        # Step 3: Generate access and refresh tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        logger.info(f"✅ Tokens generated for user: {email}")

        # Step 4: Store refresh token metadata (same as login endpoint)
        refresh_tokens = user.refresh_tokens or []
        refresh_tokens.append({
            "token_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_agent": "email_verification_auto_login"
        })
        
        # Keep only last 5 refresh tokens
        if len(refresh_tokens) > 5:
            refresh_tokens = refresh_tokens[-5:]
        
        await UserCRUD.update_refresh_tokens(db, user, refresh_tokens)
        await db.commit()  # ✅ ADDED: Commit the transaction

        logger.info(f"✅ Auto-login successful for verified user: {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "message": "Auto-login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"========== AUTO-LOGIN ERROR ==========")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auto-login failed. Please try logging in manually."
        )


@router.post("/verify-and-login")
async def verify_and_login(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-login after email verification.
    Called from the frontend after user clicks verification link in email.

    Args:
        request: Dictionary with firebase_id_token
        db: Database session

    Returns:
        access_token: Short-lived token (15 min) - stored in memory only
        refresh_token: Longer-lived token for localStorage
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        firebase_id_token = request.get('firebase_id_token')
        
        if not firebase_id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firebase ID token is required"
            )
        
        # Verify the Firebase token
        decoded_token = firebase_auth.verify_id_token(firebase_id_token)
        email = decoded_token.get('email')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in token"
            )
        
        # Check if email is verified in Firebase
        firebase_user = firebase_auth.get_user_by_email(email)
        
        if not firebase_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified"
            )
        
        logger.info(f"Email verified for user: {email}")
        
        # Get user from PostgreSQL
        user = await UserCRUD.get_by_email(db, email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate both access and refresh tokens (matching existing auth)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=refresh_token_expires
        )
        
        logger.info(f"Auto-login successful for verified user: {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "email": email,
            "message": "Auto-login successful"
        }
        
    except firebase_auth.InvalidIdTokenError:
        logger.error("Invalid Firebase token in verify_and_login")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
    except firebase_auth.ExpiredIdTokenError:
        logger.error("Expired Firebase token in verify_and_login")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token has expired"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Auto-login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auto-login failed"
        )


@router.post("/resend-verification")
async def resend_verification(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link.
    Allows users to request another verification email if they didn't receive it.
    
    Args:
        request: Password reset request with email
        db: Database session
        
    Returns:
        Success message
        
    Note:
        Returns generic message to prevent email enumeration.
    """
    email = request.email.lower().strip()
    
    try:
        # Check if user exists in PostgreSQL
        user = await UserCRUD.get_by_email(db, email)
        
        generic_message = "If an account exists for that email, a verification email has been sent."
        
        if not user:
            logger.info(f"Verification resend attempted for non-existent email: {email}")
            return {"message": generic_message}
        
        # Check if user registered via Google OAuth (skip verification for them)
        if user.auth_provider == 'google':
            logger.info(f"Google OAuth user tried to resend verification: {email}")
            return {"message": "This account was registered with Google and is already verified."}
        
        # Check if user exists in Firebase
        firebase_user = None
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            
            if firebase_user.email_verified:
                logger.info(f"Email already verified for: {email}")
                return {"message": "Email is already verified. You can login now."}
        except firebase_auth.UserNotFoundError:
            # Create Firebase user if doesn't exist (legacy users)
            try:
                firebase_user = firebase_auth.create_user(
                    email=email,
                    email_verified=False
                )
                logger.info(f"Created Firebase user for verification: {email}")
            except Exception as e:
                logger.error(f"Failed to create Firebase user: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize email verification"
                )
        
        # Send verification email via Firebase REST API with ID token
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if not FIREBASE_WEB_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service not configured"
            )
        
        try:
            # Get custom token
            custom_token = firebase_auth.create_custom_token(firebase_user.uid)
            
            # Exchange for ID token
            token_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
            token_response = requests.post(token_url, json={
                "token": custom_token.decode('utf-8'),
                "returnSecureToken": True
            })
            
            if token_response.status_code != 200:
                logger.error(f"❌ Failed to get ID token: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize email verification"
                )
            
            id_token = token_response.json().get('idToken')
            
            # Send verification email
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
            payload = {
                "requestType": "VERIFY_EMAIL",
                "idToken": id_token
            }

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                logger.info(f"✅ Verification email sent to {email}")
                return {"message": "Verification email sent! Please check your inbox.", "success": True}
            else:
                logger.error(f"❌ Failed to send verification email: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in resend verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while sending verification email"
            )
                
    except firebase_auth.FirebaseError as e:
        logger.error(f"Firebase error in resend_verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in resend_verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending email"
        )
