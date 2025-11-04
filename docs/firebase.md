# Complete Step-by-Step Guide

**NOTE-- During Normal Login (before or after password reset):Your app checks your own DB (PostgreSQL ONLY) . Firebase is **NOT involved** in your normal login flow. It's only used for the password reset email service.**

**Visual Flow Diagram --- for Password Reset**
```
[User] → [Your React: Forgot Password Page]
            ↓
[Your FastAPI: Check PostgreSQL]
            ↓
[Your FastAPI → Firebase: Create user if needed]
            ↓
[Your FastAPI → Firebase: Generate reset link]
            ↓
[Firebase: Send Email] → [Users Inbox]
            ↓
[User clicks link] → [Your React: Reset Password Page]
            ↓
[Your React → Firebase: Verify code & reset password]
            ↓
[Your React → Firebase: Sign in to get token]
            ↓
[Your React → Your FastAPI: Send token + new password(sent over https in production)]
            ↓
[Your FastAPI → Firebase: Verify token]
            ↓
[Your FastAPI → PostgreSQL: Update password(hashed on backend not on frontend)]
            ↓
[User can login with new password!]

# User logs in with email + new password
# Your backend checks YOUR PostgreSQL database

user = query("SELECT * FROM users WHERE email = ? AND password = ?")

```

---

## Part 1: Firebase Setup

### **Step 1.1: Create Firebase Project** (✅ already completed)
- Go to Firebase Console  
- Click **"Add project"** and follow the setup wizard  
- Give your project a name (e.g., `veda`)

---

### **Step 1.2: Enable Email/Password Authentication** (✅ already completed)
- In Firebase Console, click **Authentication** in the left sidebar  
- Go to **Sign-in method** tab  
- Click on **Email/Password** provider  
- Toggle **Enable** (✅ only the first option — NOT *Email Link*)  
- Click **Save**

---

### **Step 1.3: Generate Service Account Key** (✅ already completed)
- Click the gear icon (⚙️) next to **Project Overview**
- Select **Project settings**
- Go to **Service accounts** tab
- Click **Generate new private key**
- Click **Generate key** — (a JSON file will download ✅)

📌 Save this file as: `firebase-credentials.json`
📍 Location → Your FastAPI project root  
🚫 **Never commit this file to Git — add it to `.gitignore`**

---

### **Step 1.4: Configure Action URL (Password Reset Page)** (✅ already completed)
- Go to **Authentication**
- Click **Templates** tab
- Select **Password reset**
- Customize email template (optional)

- **Action URL will be set later when frontend reset page is ready**

---

## Part 2: Backend Setup (FastAPI)

### **Step 2.1: Install Required Packages** (✅ already completed)
```bash
pip install firebase-admin python-decouple passlib[bcrypt]
```
---

### **Step 2.2: Create Firebase Configuration File** (✅ already completed)
- Create: `app/firebase_config.py`
```python
import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)

def get_firebase_auth():
    """Returns Firebase Auth instance"""
    return auth
```

---

### **Step 2.3: Create Password Reset Endpoint**
- In `app/main.py` or `app/api/routers/auth.py`:
```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth
from firebase_config import get_firebase_auth
import logging

# Your existing database imports
# from database import get_db_connection

router = APIRouter()
logger = logging.getLogger(__name__)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Handle forgot password request.
    Generates Firebase password reset link and sends email.
    """
    email = request.email.lower().strip()
    
    try:
        # Step 1: Check if user exists in YOUR PostgreSQL database
        user_exists = await check_user_exists_in_postgres(email)
        
        # SECURITY: Always return same message regardless of whether user exists
        generic_message = "If an account exists for that email, a password reset link has been sent."
        
        if not user_exists:
            logger.info(f"Password reset attempted for non-existent email: {email}")
            return {"message": generic_message}
        
        # Step 2: Check if user exists in Firebase (create if needed)
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            # Create user in Firebase with a random password
            # They'll set their actual password via the reset link
            firebase_user = firebase_auth.create_user(
                email=email,
                email_verified=True
            )
            logger.info(f"Created Firebase user for password reset: {email}")
        
        # Step 3: Generate password reset link
        reset_link = firebase_auth.generate_password_reset_link(email)
        logger.info(f"Generated password reset link for: {email}")
        
        # Firebase automatically sends email
        return {
            "message": generic_message,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )

async def check_user_exists_in_postgres(email: str) -> bool:
    """
    Check if user exists in your PostgreSQL database.
    Replace this with your actual database query.
    """
    return True  # TO D0: real db check

```

---

### **Step 2.4: Add Endpoint to Update Password in PostgreSQL**
- This endpoint will be called AFTER the user resets their password via Firebase:
- In `app/main.py` or  `app/api/routers/auth.py`:
```python
from fastapi import Header
from passlib.context import CryptContext

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UpdatePasswordRequest(BaseModel):
    firebase_id_token: str
    new_password: str  # Plain password from frontend

@router.post("/sync-password")
async def sync_password_with_postgres(request: UpdatePasswordRequest):
    """
    After Firebase password reset, update password in PostgreSQL.
    Verifies Firebase ID token for security.
    """
    try:
        # Backend verifies the Firebase token (security check)
        decoded_token = firebase_auth.verify_id_token(request.firebase_id_token)
        email = decoded_token['email']
        
        # Hash password on backend (secure)
        password_hash = pwd_context.hash(request.new_password)

        # Update password in PostgreSQL database
        success = await update_password_in_postgres(email, password_hash)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        return {"message": "Password updated successfully"}
        
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
    except Exception as e:
        logger.error(f"Error syncing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating password"
        )

async def update_password_in_postgres(email: str, password_hash: str) -> bool:
    """
    Update user password in PostgreSQL database.
    """
    return True  # TO DO: real update logic

```

---

### **Step 2.5: Add Resend Password Reset Link Endpoint**

**In `app/api/routers/auth.py`:**

- This allows users to request another password reset email if they didn't receive the first one.
```python
@router.post("/resend-password-reset")
async def resend_password_reset(request: ForgotPasswordRequest):
    """
    Resend password reset link
    Same logic as forgot-password endpoint
    """
    email = request.email.lower().strip()
    
    try:
        # Check if user exists in PostgreSQL
        user_exists = await check_user_exists_in_postgres(email)
        
        generic_message = "If an account exists for that email, a password reset link has been sent."
        
        if not user_exists:
            logger.info(f"Password reset resend attempted for non-existent email: {email}")
            return {"message": generic_message}
        
        # Check if user exists in Firebase
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            firebase_user = firebase_auth.create_user(
                email=email,
                email_verified=True
            )
            logger.info(f"Created Firebase user for password reset: {email}")
        
        # Generate new password reset link
        reset_link = firebase_auth.generate_password_reset_link(email)
        logger.info(f"Resent password reset link for: {email}")
        
        return {
            "message": generic_message,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error resending password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later."
        )
```

---


## Part 3: Frontend Setup (React)

### **Step 3.1: Install Firebase Client SDK** (✅ already completed)
```bash
npm install firebase

```
---

### **Step 3.2: Create Firebase Config File** (✅ already completed)
- Create: `src/firebase.js`
```javascript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Get these from Firebase Console > Project Settings > General
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

```

---


### **Step 3.3: Forgot Password Component**
- Create: `src/components/ForgotPassword.jsx`
```javascript
import React, { useState } from 'react';
import axios from 'axios';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showResend, setShowResend] = useState(false);

  const handleForgotPassword = async (e, isResend = false) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const endpoint = isResend ? '/resend-password-reset' : '/forgot-password';
      const response = await axios.post('http://localhost:8000${endpoint}', {
        email: email
      });

      setMessage(response.data.message);
      setShowResend(true); // Show resend option after first send
      if (!isResend) setEmail(''); // Clear input only on first send
    } catch (err) {
      setError('An error occurred. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-password-container">
      <h2>Forgot Password</h2>
      <form onSubmit={(e) => handleForgotPassword(e, false)}>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={loading}
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>

      {message && ( /* Add opening parenthesis */
        <div> 
          <p className="success-message">{message}</p>
          {showResend && (
            <button 
              onClick={(e) => handleForgotPassword(e, true)}
              disabled={loading}
              className="resend-button"
              style={{ marginTop: '10px' }} // Optional styling
            >
              Didn't receive email? Resend
            </button>
          )}
        </div> 
      )} 
      
      {error && <p className="error-message">{error}</p>}

      <a href="/login">Back to Login</a>
    </div>
  );
};

export default ForgotPassword;

```

---

### **Step 3.4: Reset Password Component**
- Create: `src/components/ResetPassword.jsx`
```javascript
import React, { useState, useEffect } from 'react';
import { auth } from '../firebase';
import { confirmPasswordReset, verifyPasswordResetCode, signInWithEmailAndPassword } from 'firebase/auth';
import axios from 'axios';
import { useNavigate, useSearchParams } from 'react-router-dom';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [codeVerified, setCodeVerified] = useState(false);

  const oobCode = searchParams.get('oobCode'); // Firebase sends this in the URL

  useEffect(() => {
    // Verify the reset code when component mounts  
    if (oobCode) {
      verifyPasswordResetCode(auth, oobCode)
        .then((email) => {
          setEmail(email);
          setCodeVerified(true);
        })
        .catch((error) => {
          setError('Invalid or expired reset link');
          console.error(error);
        });
    } else {
      setError('No reset code provided');
    }
  }, [oobCode]);

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Step 1: Reset password in Firebase
      await confirmPasswordReset(auth, oobCode, newPassword);
      
      // Step 2: Sign in to get Firebase ID token
      const userCredential = await signInWithEmailAndPassword(auth, email, newPassword);
      const idToken = await userCredential.user.getIdToken();
      
      // Step 3: Send plain password to backend (will be hashed there)
      await axios.post('http://localhost:8000/sync-password', {
        firebase_id_token: idToken,
        new_password: newPassword  // Backend will hash this
    });

      alert('Password reset successful! You can now log in with your new password.');
      navigate('/login');
      
    } catch (err) {
      console.error('Error resetting password:', err);
      setError('Failed to reset password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!codeVerified) {
    return (
      <div className="reset-password-container">
        <p>{error || 'Verifying reset code...'}</p>
      </div>
    );
  }

  return (
    <div className="reset-password-container">
      <h2>Reset Password</h2>
      <p>Enter your new password for {email}</p>
      
      <form onSubmit={handleResetPassword}>
        <input
          type="password"
          placeholder="New Password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          disabled={loading}
          minLength={6}
        />
        
        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          disabled={loading}
          minLength={6}
        />
        
        <button type="submit" disabled={loading}>
          {loading ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>

      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default ResetPassword;
```

---

### **Step 3.5: Configure Action URL in Firebase**
- Go to Firebase Console → Authentication → Templates
- Edit: Password reset template

Set Action URL:
```bash
 # Replace with your real frontend URL
http://localhost:5173/reset-password

```
- Save ✅

---

### **Step 3.6: Add Routes**
- Modify App.js:
```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Your existing routes */}
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Part 4: Security Considerations 
- ✅ Add to .gitignore : `firebase-credentials.json` 
- ✅ Add to .env : FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

- Update `firebase_config.py`: (✅ already completed)
```python
from decouple import config
cred = credentials.Certificate(config('FIREBASE_CREDENTIALS_PATH'))
```
- Enable CORS in FastAPI
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---


## Part 5: Enabling Email Verification feature

### **Overview:**
Firebase can automatically send email verification when users sign up. This ensures users have access to their email address.

### **Important Clarification:**
- **Normal Login:** Your app ONLY checks PostgreSQL for credentials. Firebase is NOT involved.
- **Verification Check:** Your backend makes ONE quick API call to Firebase to check `email_verified` status
- **No Firebase Authentication:** Users don't authenticate "through" Firebase - they authenticate through YOUR PostgreSQL
- **Firebase's Role:** Only used for:
  1. Sending verification emails
  2. Storing `email_verified` flag
  3. Sending password reset emails

**After email verification:**
- User's `email_verified` flag in Firebase = `true`
- User can login normally via YOUR PostgreSQL database
- Backend checks verification status once during login (quick API call)
- No ongoing Firebase involvement in authentication flow

---

### **Step 5.1: Enable Email Verification in Firebase Console** (✅ already completed)
- Go to Firebase Console → Authentication → Templates
- Click on **Email address verification** template
- Customize the email template if needed

- **The action URL should point to your app (will be handled automatically)**

---

### **Step 5.2: Update Backend - Send Verification on User Creation**

**In `app/api/routers/auth.py` (or wherever you create new users):**

Add this function to send verification email:
```python
@router.post("/signup")
async def signup(request: SignupRequest):
    """
    User signup - creates user in PostgreSQL and Firebase

    Note: This signup endpoint is for email/password users only. Google Sign-In users follow a different flow and don't need email verification.

    """
    email = request.email.lower().strip()
    password = request.password
    
    try:
        # Step 1: Hash password
        password_hash = pwd_context.hash(password)
        
        # Step 2: Create user in PostgreSQL
        user_created = await create_user_in_postgres(email, password_hash)
        
        if not user_created:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        # Step 3: Create user in Firebase
        firebase_user = firebase_auth.create_user(
            email=email,
            password=password,  # Firebase needs the plain password
            email_verified=False  # Not verified yet
        )
        
        # Step 4: Generate and send verification email
        verification_link = firebase_auth.generate_email_verification_link(email)
        logger.info(f"Verification email sent to: {email}")
        
        # Firebase automatically sends the email!
        
        return {
            "message": "Account created! Please check your email to verify your account.",
            "email": email
        }
        
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating account"
        )

@router.post("/verify-and-login")
async def verify_and_login(request: dict):
    """
    Auto-login after email verification

    Returns:
    - access_token: Short-lived token (15 min) - stored in memory only
    - You may also want to return a refresh_token here for localStorage
    """
    try:
        firebase_id_token = request.get('firebase_id_token')
        
        # Verify the Firebase token
        decoded_token = firebase_auth.verify_id_token(firebase_id_token)
        email = decoded_token['email']
        
        # Check if email is verified in Firebase
        firebase_user = firebase_auth.get_user_by_email(email)
        
        if not firebase_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified"
            )
        
        # Get user from PostgreSQL
        user = await get_user_from_postgres(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate both access and refresh tokens (matching your existing auth)
        access_token = create_access_token(user)  # 15 min
        refresh_token = create_refresh_token(user)  # Longer lived token
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Add this
            "email": email,
            "message": "Auto-login successful"
        }
        
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
    except Exception as e:
        logger.error(f"Auto-login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auto-login failed"
        )

async def get_user_from_postgres(email: str):
    """
    Get user from PostgreSQL database
    """
    # TODO: Implement your actual database query
    # Query: SELECT * FROM users WHERE email = 'email'
    return {"email": email}  # Placeholder

def create_refresh_token(user):
    """
    Create JWT refresh token
    """
    # TODO: Implement your refresh token creation
    # Should match your existing implementation
    return "your_refresh_token_here"  # Placeholder

def create_access_token(user):
    """
    Create JWT access token for your app
    """
    # TODO: Implement your JWT token creation
    # Use your existing token creation logic
    return "your_jwt_token_here"  # Placeholder

```

---

### **Step 5.3: Frontend - Email Verification Handler**

**Create: `src/components/VerifyEmail.jsx`**
```javascript
import React, { useEffect, useState } from 'react';
import { auth } from '../firebase';
import { applyActionCode } from 'firebase/auth';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [verifying, setVerifying] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const oobCode = searchParams.get('oobCode');

  useEffect(() => {
    if (!oobCode) {
      setError('Invalid verification link');
      setVerifying(false);
      return;
    }

    // Apply the email verification code
    applyActionCode(auth, oobCode)
      .then(async () => {
        setSuccess(true);
        
        // Auto-login: Get user email from Firebase
        const user = auth.currentUser;
        if (user) {
          try {
            // Get Firebase ID token
            const idToken = await user.getIdToken();
            
            // Call your backend to auto-login
            const response = await axios.post(
              `${import.meta.env.VITE_API_BASE}/verify-and-login`,
              { firebase_id_token: idToken }
            );
            
            // Store tokens following your existing auth pattern:
            // - Access token: Keep in memory (via state/context)
            // - Refresh token: Store in localStorage

            // Store refresh token in localStorage (if returned)
            if (response.data.refresh_token) {
            localStorage.setItem('refresh_token', response.data.refresh_token);
            }

            // Pass access token via navigation state (stays in memory)
            navigate('/chatpage', { 
            state: { 
                access_token: response.data.access_token,
                autoLogin: true 
            }
            });

            // OR if you have an auth context that handles token storage:
            // authContext.login(response.data.access_token, response.data.refresh_token);
            // navigate('/chatpage');
            
          } catch (error) {
            console.error('Auto-login failed:', error);
            setError('Verification successful, but auto-login failed. Please login manually.');
            setTimeout(() => navigate('/login'), 3000);
          }
        }
        
        setVerifying(false);
      })

      .catch((error) => {
        console.error('Verification error:', error);
        setError('Verification failed. Link may be expired or invalid.');
        setVerifying(false);
      });
  }, [oobCode, navigate]);

  if (verifying) {
    return (
      <div className="verify-email-container">
        <h2>Verifying your email...</h2>
        <p>Please wait...</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="verify-email-container">
        <h2>✅ Email Verified!</h2>
        <p>Your email has been successfully verified.</p>
        <p>Logging you in automatically...</p>
      </div>
    );
  }

  return (
    <div className="verify-email-container">
      <h2>❌ Verification Failed</h2>
      <p>{error}</p>
      <a href="/login">Go to Login</a>
    </div>
  );
};

export default VerifyEmail;
```

**Security Note (Token Storage):** 
Your app already follows security best practices:
- ✅ **Access tokens** stored in **memory only** (never in localStorage)
- ✅ **Refresh tokens** stored in **localStorage** (used to get new access tokens)
- ✅ Access tokens are **short-lived (15 minutes)**

**Implementation for Auto-Login:**
After email verification, the access token should be passed to your existing auth context/state management system, NOT stored in localStorage. The token will remain in memory for the session duration.

**How it works:**
1. User verifies email
2. Backend returns short-lived access token (15 min)
3. Token passed via navigation state OR auth context
4. Token stored in memory (React state/context)
5. When token expires, refresh token (from localStorage) gets new access token (15 min)

---


### **Step 5.4: Update Routes**

**In `App.js`, add the verify-email route:**
```javascript
import VerifyEmail from './components/VerifyEmail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Existing routes */}
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        
        {/* Add this new route */}
        <Route path="/verify-email" element={<VerifyEmail />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

### **Step 5.5: Configure Action URL in Firebase**

**Set the verification action URL:**

1. Go to Firebase Console → Authentication → Templates
2. Click edit on **Email address verification** template
3. Set Action URL to:
```
   http://localhost:5173/verify-email
```
   (or your production URL: `https://yourdomain.com/verify-email`)
4. Save ✅

---


### **Step 5.6: Update Login Endpoint (Verification Check)**

**Update your existing login endpoint to check verification status:**
```python
@router.post("/login")
async def login(request: LoginRequest):
    """
    User login - check email verification status

    Flow:
    1. Check credentials in YOUR PostgreSQL (main authentication)
    2. Make quick Firebase API call to check email_verified flag
    3. If verified, issue YOUR app's JWT token
    
    Firebase is NOT authenticating the user - just checking verification status.
    """
    email = request.email.lower().strip()
    password = request.password

    try:
        # Step 1: Verify credentials in PostgreSQL
        user = await authenticate_user(email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Step 2: Check if email is verified in Firebase
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            
            if not firebase_user.email_verified:
                # User exists in Firebase but email not verified
                # Resend verification email
                try:
                    verification_link = firebase_auth.generate_email_verification_link(email)
                    logger.info(f"Resent verification email to unverified user: {email}")
                except Exception as e:
                    logger.error(f"Error sending verification email: {str(e)}")

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email before logging in. A new verification email has been sent to your inbox."
                )
        except firebase_auth.UserNotFoundError:
            # User exists in PostgreSQL but not Firebase
            # Create user in Firebase and send verification email
            logger.warning(f"User {email} exists in PostgreSQL but not in Firebase")

            try:
                # Create Firebase user
                firebase_user = firebase_auth.create_user(
                    email=email,
                    email_verified=False
                )
                
                # Send verification email
                verification_link = firebase_auth.generate_email_verification_link(email)
                logger.info(f"Created Firebase user and sent verification email to: {email}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your email is not verified. A verification email has been sent to your inbox. Please verify your email and try logging in again."
                )
            except Exception as e:
                logger.error(f"Error creating Firebase user for {email}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing login. Please try again."
                )
        
        # Step 3: Generate your app's auth token
        access_token = create_access_token(user)
        
        return {
            "access_token": access_token,
            "email": email
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

```
**Complete Login Flow Summary**
```
[User Login Attempt]
      ↓
[Check PostgreSQL Credentials]
      ↓
  Valid? ─── NO ──→ [Return "Invalid Credentials"]
      ↓
     YES
      ↓
[Check Firebase User Exists?]
      ↓
   EXISTS ────────────────────┐
      ↓                       ↓
[Check email_verified?]    [User Not in Firebase]
      ↓                       ↓
VERIFIED ─→ [Login Success] [Create Firebase User]
      ↓                       ↓
  NOT VERIFIED              [Send Verification Email]
      ↓                       ↓
[RESEND Verification Email] [Block Login]
      ↓                       ↓
[Block Login]              [Error: "Check Email to Verify"]
      ↓
[Error: "New Email Sent - Verify"]
      
```

**Note:** This prevents unverified users from logging in manually, but allows verified users to login normally.

**Handling Users Created Before Firebase Integration**

**Scenario:** User exists in PostgreSQL but not in Firebase (created before Firebase integration or manually added).

**Flow:**
1. User tries to login
2. Backend checks PostgreSQL ✅ (credentials valid)
3. Backend checks Firebase ❌ (user doesn't exist)
4. Backend automatically:
   - Creates user in Firebase with `email_verified=False`
   - Sends verification email
   - Returns error asking user to verify email
5. User clicks verification link in email
6. User is auto-logged in (via Step 5.3 flow)

**Code already implemented in Step 5.6 above.**

---

### **Step 5.6.1: Google Sign-In Users - No Verification Required**

**Important:** Google Sign-In users do NOT need email verification because:
- Google has already verified their email address
- You trust Google's verification process

**Update your login endpoint to skip Firebase verification for Google users:**
```python
@router.post("/login")
async def login(request: LoginRequest):
    """
    User login - check email verification status
    Only applies to email/password users, NOT Google sign-in users
    """
    email = request.email.lower().strip()
    password = request.password
    
    try:
        # Step 1: Authenticate user in PostgreSQL
        user = await authenticate_user(email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Step 2: Check if user signed up with Google
        # If so, skip Firebase verification check
        if user.get('auth_provider') == 'google':  # or however you track this
            # Google users are pre-verified, skip Firebase check
            access_token = create_access_token(user)
            return {
                "access_token": access_token,
                "email": email
            }
        
        # Step 3: For email/password users, check Firebase verification
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            
            if not firebase_user.email_verified:
                # Resend verification email
                try:
                    verification_link = firebase_auth.generate_email_verification_link(email)
                    logger.info(f"Resent verification email to unverified user: {email}")
                except Exception as e:
                    logger.error(f"Error sending verification email: {str(e)}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email before logging in. A new verification email has been sent to your inbox."
                )
                
        except firebase_auth.UserNotFoundError:
            # User exists in PostgreSQL but not Firebase
            # Create Firebase user and send verification
            logger.warning(f"User {email} exists in PostgreSQL but not in Firebase")
            
            try:
                firebase_user = firebase_auth.create_user(
                    email=email,
                    email_verified=False
                )
                
                verification_link = firebase_auth.generate_email_verification_link(email)
                logger.info(f"Created Firebase user and sent verification email to: {email}")
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your email is not verified. A verification email has been sent to your inbox. Please verify your email and try logging in again."
                )
            except Exception as e:
                logger.error(f"Error creating Firebase user for {email}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing login. Please try again."
                )
        
        # Step 4: Email verified, issue access token
        access_token = create_access_token(user)
        
        return {
            "access_token": access_token,
            "email": email
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
```

**Key Change:** Added check for `auth_provider` - if it's 'google', skip Firebase verification.

---

### **How to Track Auth Provider in PostgreSQL**

**Update your users table to include `auth_provider` column:**
```sql
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'email';
-- Values: 'email' or 'google'
```

**When creating user via Google Sign-In:**
```python
# In your Google sign-in endpoint
await create_user_in_postgres(
    email=email,
    password_hash=None,  # No password for Google users
    auth_provider='google'
)
```

**When creating user via Email/Password:**
```python
# In your signup endpoint
await create_user_in_postgres(
    email=email,
    password_hash=hashed_password,
    auth_provider='email'
)
```

---

### **Step 5.6.2: What About Users Who Reset Password?**

**Question:** If a user resets their password via Firebase, can they login?

**Answer:** Yes! Here's why:

1. **During Password Reset (Step 2.3):**
   - When creating Firebase user for password reset, we set `email_verified=True`:
```python
   firebase_user = firebase_auth.create_user(
       email=email,
       email_verified=True  # ← Already verified!
   )
```

2. **After Password Reset:**
   - User's Firebase account has `email_verified=True`
   - User resets password successfully
   - User goes to login page
   - Login endpoint checks PostgreSQL credentials ✅
   - Login endpoint checks Firebase verification status ✅ (already true)
   - User logs in successfully

**Summary:** Users who reset passwords are automatically marked as verified in Firebase, so they can login without issues.

---

### **Step 5.7: Resend Verification Email**

**Add endpoint to resend verification:**
```python
@router.post("/resend-verification")
async def resend_verification(request: ForgotPasswordRequest):
    """
    Resend email verification link
    """
    email = request.email.lower().strip()
    
    try:
        # Check if user exists in Firebase
        firebase_user = firebase_auth.get_user_by_email(email)
        
        if firebase_user.email_verified:
            return {"message": "Email is already verified"}
        
        # Generate new verification link
        verification_link = firebase_auth.generate_email_verification_link(email)
        
        return {"message": "Verification email sent!"}
        
    except firebase_auth.UserNotFoundError:
        # Don't reveal if user exists
        return {"message": "If account exists, verification email sent"}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending email")
```

---

### **Frontend: Add Resend Button**

**Create: `src/components/ResendVerification.jsx`**
```javascript
import React, { useState } from 'react';
import axios from 'axios';

const ResendVerification = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleResend = async (e) => {
    e.preventDefault();
    
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE}/resend-verification`,
        { email }
      );
      
      setMessage(response.data.message);
    } catch (error) {
      setMessage('Error sending email. Please try again.');
    }
  };

  return (
    <div>
      <h3>Resend Verification Email</h3>
      <form onSubmit={handleResend}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
        />
        <button type="submit">Resend</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
};

export default ResendVerification;
```

---

### **Email Verification Flow:**
```
[User Signs Up with Email/Password]
      ↓
[Backend: Create user in PostgreSQL & Firebase]
      ↓
[Backend: Generate verification link via Firebase]
      ↓
[Firebase: Send verification email]
      ↓
[User clicks link in email]
      ↓
[Opens: /verify-email?oobCode=...]
      ↓
[React: Verify code with Firebase]
      ↓
[Firebase: Mark email as verified]
      ↓
[React: Auto-login with Firebase token]
      ↓
[Backend: Verify token & issue app token]
      ↓
[User automatically logged in! ✅]
      ↓
[Redirect to chat page]
```

### **Google Sign-In Users:**
```
[Sign In with Google]
      ↓
[Google Verifies Email] ← Already done by Google
      ↓
[Create in PostgreSQL ONLY]
      ↓
[Auto Login Immediately]
      ↓
[Can login anytime with Google] ← No Firebase verification needed
```

---

### **Notes:**
- Email verification is **required** - users must verify before logging in
- After verification, users are **automatically logged in** (no manual login needed)
- Firebase sends the email automatically (like password reset)
- The verification link expires in 3 days (Firebase default)
- Users can request a new verification email if expired
- Manual login will check verification status and block unverified users
- Password reset flow does NOT auto-login (users must login manually after reset)
- **If user exists in PostgreSQL but not in Firebase:** System automatically creates Firebase user, sends verification email, and blocks login until verified
- **Google Sign-In users:** Do NOT require email verification (Google already verified their email)

---


## **Testing the Flow**

- 1️⃣ Start FastAPI
```bash
cd backend
uvicorn main:app --reload
```
- 2️⃣ Start React
```bash
npm start

```
- 3️⃣ Visit → /forgot-password
- 4️⃣ Enter email from PostgreSQL DB
- 5️⃣ Check inbox → Reset link received ✅
- 6️⃣ Click → Opens /reset-password?oobCode=...
- 7️⃣ Reset password → ✅ Saved in Firebase + PostgreSQL