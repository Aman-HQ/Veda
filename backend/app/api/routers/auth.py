"""
Authentication endpoints for user registration, login, and token management.
"""
from datetime import timedelta, datetime, timezone
from typing import Dict, Any
from uuid import UUID, uuid4
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

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
    GoogleOAuthRequest
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
    
    Args:
        user_create: User registration data
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = await UserCRUD.get_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        user = await UserCRUD.create(db, user_create)
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
    
    Args:
        login_request: Login credentials
        request: HTTP request for extracting user agent
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = await UserCRUD.authenticate(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
            logger.info(f"Existing user logged in via OAuth: {user_email}")

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
    
