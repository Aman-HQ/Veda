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
- **Firebase uses **ONE action URL** for all email actions (password reset, email verification, etc.). The URL receives different `mode` parameters to distinguish actions.**

---

## Part 2: Backend Setup (FastAPI)

### **Step 2.1: Install Required Packages** (✅ already completed)
```bash
pip install firebase-admin python-decouple passlib[bcrypt] requests
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
    
    logger.info(f"========== FORGOT PASSWORD REQUEST ==========")
    logger.info(f"Email received: {email}")

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
        # reset_link = firebase_auth.generate_password_reset_link(email)
        # logger.info(f"Generated password reset link for: {email}")
        
        # Step 3: Send password reset email using Firebase REST API
        FIREBASE_WEB_API_KEY ="AIzaSyAtzGoi--CIrt0ronBzo12W32G2qpHe7NA" #Your API key
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            logger.info(f"✅ Password reset email sent successfully to {email}")
            logger.info(f"Firebase response: {response.json()}")
        else:
            logger.error(f"❌ Firebase email sending failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )

        logger.info(f"========== REQUEST COMPLETED SUCCESSFULLY ==========")

        # Firebase automatically sends email
        return {
            "message": generic_message,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"========== ERROR IN FORGOT PASSWORD ==========")
        logger.error(f"Error: {str(e)}", exc_info=True)
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
**Important:** 
- Firebase Admin SDK's `generate_password_reset_link()` does NOT send emails automatically
- We use Firebase REST API's `sendOobCode` endpoint to trigger email sending
- This requires your Firebase Web API Key (same one used in frontend config)
- Firebase will send the email using your configured email template

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
        
        # # Generate new password reset link
        # reset_link = firebase_auth.generate_password_reset_link(email)
        # logger.info(f"Resent password reset link for: {email}")
        
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
      const response = await axios.post(`http://localhost:8000${endpoint}`, {
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

### **Step 3.4: Create Unified Auth Action Handler**

**Create: `src/components/AuthAction.jsx`**

- This single component handles ALL Firebase email actions (password reset, email verification, etc.)

```javascript
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { auth } from '../firebase';
import { 
  confirmPasswordReset, 
  verifyPasswordResetCode, 
  applyActionCode,
  signInWithEmailAndPassword 
} from 'firebase/auth';
import axios from 'axios';
import AuthLayout from '../components/Layout/AuthLayout.jsx';
import authStore from '../stores/authStore';

export default function AuthAction() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Common states
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Password reset specific states
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [email, setEmail] = useState('');
  
  // Get parameters from URL
  const mode = searchParams.get('mode');
  const oobCode = searchParams.get('oobCode');
  const apiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    // Validate parameters
    if (!mode || !oobCode) {
      setError('Invalid action link. Please check your email and try again.');
      setVerifying(false);
      return;
    }

    // Route to appropriate handler based on mode
    switch (mode) {
      case 'resetPassword':
        handlePasswordResetVerification();
        break;
      case 'verifyEmail':
        handleEmailVerification();
        break;
      case 'recoverEmail':
        setError('Email recovery is not yet supported. Please contact support.');
        setVerifying(false);
        break;
      default:
        setError(`Unknown action type: ${mode}`);
        setVerifying(false);
    }
  }, [mode, oobCode]);

  // ========== PASSWORD RESET HANDLERS ==========
  
  const handlePasswordResetVerification = async () => {
    try {
      const userEmail = await verifyPasswordResetCode(auth, oobCode);
      setEmail(userEmail);
      setVerifying(false);
    } catch (error) {
      console.error('Password reset verification error:', error);
      
      // Handle specific Firebase errors
      if (error.code === 'auth/invalid-action-code') {
        setError('This password reset link is invalid or has already been used.');
      } else if (error.code === 'auth/expired-action-code') {
        setError('This password reset link has expired. Please request a new one.');
      } else {
        setError('Invalid or expired password reset link. Please request a new one.');
      }
      setVerifying(false);
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      // Step 1: Reset password in Firebase
      await confirmPasswordReset(auth, oobCode, newPassword);
      console.log('Password reset in Firebase successful');
      
      // Step 2: Sign in to get Firebase ID token
      const userCredential = await signInWithEmailAndPassword(auth, email, newPassword);
      const idToken = await userCredential.user.getIdToken();
      console.log('Got Firebase ID token');
      
      // Step 3: Sync with PostgreSQL
      await axios.post(`${apiBase}/api/auth/sync-password`, {
        firebase_id_token: idToken,
        new_password: newPassword
      });
      console.log('Password synced to PostgreSQL');

      setSuccess(true);
      
      // Navigate to login after success
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Password reset successful! You can now log in with your new password.',
            type: 'success'
          } 
        });
      }, 2000);
      
    } catch (err) {
      console.error('Error resetting password:', err);
      
      // Handle specific errors
      if (err.response?.status === 401) {
        setError('Authentication failed. Please try resetting your password again.');
      } else if (err.response?.status === 404) {
        setError('User account not found. Please contact support.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.code === 'auth/weak-password') {
        setError('Password is too weak. Please use a stronger password.');
      } else if (err.code === 'auth/invalid-action-code') {
        setError('This reset link has already been used. Please request a new one.');
      } else {
        setError('Failed to reset password. Please try again or request a new reset link.');
      }
      setLoading(false);
    }
  };

  // ========== EMAIL VERIFICATION HANDLERS ==========

  const handleEmailVerification = async () => {
    try {
      // Apply the email verification code
      await applyActionCode(auth, oobCode);
      setSuccess(true);
      
      // Auto-login after verification
      const user = auth.currentUser;
      if (user) {
        try {
          // Get Firebase ID token
          const idToken = await user.getIdToken();
          
          // Call backend to auto-login
          const response = await axios.post(
            `${apiBase}/api/auth/verify-and-login`,
            { firebase_id_token: idToken }
          );
          
          // Store tokens using auth store
          const { access_token, refresh_token } = response.data;
          
          if (access_token && refresh_token) {
            authStore.setTokens({
              accessToken: access_token,
              refreshToken: refresh_token
            });
            
            setVerifying(false);
            
            // Navigate to chat page
            setTimeout(() => {
              navigate('/chat', { 
                replace: true,
                state: { 
                  autoLogin: true,
                  message: 'Email verified successfully!'
                }
              });
            }, 2000);
          } else {
            throw new Error('Invalid response from server');
          }
          
        } catch (error) {
          console.error('Auto-login failed:', error);
          setError('Verification successful, but auto-login failed. Please login manually.');
          setVerifying(false);
          setTimeout(() => navigate('/login'), 3000);
        }
      } else {
        setError('Verification successful! Please login to continue.');
        setVerifying(false);
        setTimeout(() => navigate('/login'), 2000);
      }
    } catch (error) {
      console.error('Email verification error:', error);
      
      // Provide user-friendly error messages
      if (error.code === 'auth/invalid-action-code') {
        setError('Verification link is invalid or has already been used.');
      } else if (error.code === 'auth/expired-action-code') {
        setError('Verification link has expired. Please request a new one.');
      } else {
        setError('Verification failed. Link may be expired or invalid.');
      }
      
      setVerifying(false);
    }
  };

  // ========== RENDER LOGIC ==========

  // Loading state while verifying code
  if (verifying) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">
              {mode === 'resetPassword' ? 'Verifying reset code...' : 'Verifying your email...'}
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // Error state - verification failed
  if (error && !success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-6 text-center">
            {mode === 'resetPassword' ? 'Reset Link Invalid' : 'Verification Failed'}
          </h1>
          <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 mb-6">
            <div className="text-center mb-3">
              <span className="text-4xl">❌</span>
            </div>
            <p className="text-sm text-red-800 dark:text-red-200 text-center">{error}</p>
          </div>
          <div className="space-y-4">
            {mode === 'resetPassword' && (
              <button
                onClick={() => navigate('/forgot-password')}
                className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Request New Reset Link
              </button>
            )}
            <button
              onClick={() => navigate('/login')}
              className="w-full py-2 px-4 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Back to Login
            </button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== EMAIL VERIFICATION SUCCESS ==========
  if (mode === 'verifyEmail' && success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              Email Verified!
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-2">
              Your email has been successfully verified.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Logging you in automatically...
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== PASSWORD RESET SUCCESS ==========
  if (mode === 'resetPassword' && success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              Password Reset Successful!
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-2">
              You can now log in with your new password.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Redirecting to login...
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== PASSWORD RESET FORM ==========
  if (mode === 'resetPassword') {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6 w-[500px] sm:w-[440px]">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-9 text-center">
            Reset Password
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 text-center">
            Enter your new password for <span className="font-medium text-slate-900 dark:text-slate-100">{email}</span>
          </p>

          <form onSubmit={handlePasswordReset} className="space-y-5">
            <label className="block" htmlFor="new-password">
              <span className="block text-sm text-slate-700 dark:text-slate-300">New Password</span>
              <input
                id="new-password"
                type="password"
                required
                minLength={8}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
                placeholder="Enter new password (min 8 characters)"
              />
            </label>

            <label className="block" htmlFor="confirm-password">
              <span className="block text-sm text-slate-700 dark:text-slate-300">Confirm Password</span>
              <input
                id="confirm-password"
                type="password"
                required
                minLength={8}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                placeholder="Confirm your new password"
              />
            </label>

            {error && (
              <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}

            {loading && !error && (
              <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  Resetting your password...
                </p>
              </div>
            )}

            <button
              type="submit"
              className="mt-2 w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Resetting Password...' : 'Reset Password'}
            </button>
          </form>

          <div className="mt-5 text-center">
            <button
              onClick={() => navigate('/login')}
              className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm"
              disabled={loading}
            >
              Back to Login
            </button>
          </div>

          <div className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
            <p>Make sure your password is at least 8 characters long.</p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // Fallback
  return null;
}
```
**Why this approach is better:**
- ✅ Single component handles all Firebase email actions
- ✅ Automatically routes based on `mode` parameter
- ✅ Matches Firebase's design (one action URL)
- ✅ Easier to maintain (one file instead of multiple)
- ✅ Can easily add new actions (email change, etc.)


---


### **Step 3.5: Configure Action URL in Firebase**

- Firebase uses **ONE action URL** for all email actions (password reset, email verification, etc.). The URL receives different `mode` parameters to distinguish actions.

**Set the unified action URL:**

1. Go to Firebase Console → Authentication → Templates → Password reset
2. Set Action URL to:
```bash
   http://localhost:5173/auth-action
```
3. Click edit on **Email address verification** template
4. Set Action URL to:
```bash
   http://localhost:5173/auth-action
```
5. Save ✅

**Note:** Both templates should point to the **same URL** (`/auth-action`). Firebase adds query parameters to distinguish actions:
- Password Reset: `?mode=resetPassword&oobCode=...`
- Email Verification: `?mode=verifyEmail&oobCode=...`

---

### **Step 3.6: Add Routes**
- Modify App.js:
```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ForgotPassword from './components/ForgotPassword';
import AuthAction from './components/AuthAction';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Your existing routes */}
        <Route path="/forgot-password" element={<ForgotPassword />} />
        
        {/* Unified handler for all Firebase email actions */}
        <Route path="/auth-action" element={<AuthAction />} />
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
        
        # # Step 4: Generate and send verification email
        # verification_link = firebase_auth.generate_email_verification_link(email)
        # logger.info(f"Verification email sent to: {email}")
        
        # Step 4: Send verification email using Firebase REST API
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if not FIREBASE_WEB_API_KEY:
            logger.error("Firebase Web API Key not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service not configured"
            )

        logger.info(f"Sending verification email via Firebase REST API...")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"

        payload = {
            "requestType": "VERIFY_EMAIL",
            "email": email
        }

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            logger.info(f"✅ Verification email sent successfully to {email}")
            logger.info(f"Firebase response: {response.json()}")
        else:
            logger.error(f"❌ Firebase email sending failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            # Don't fail user creation, just log the error
            logger.warning("User created but verification email failed to send")

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
**Important:** 
- Firebase Admin SDK's `generate_email_verification_link()` does NOT send emails automatically
- We use Firebase REST API's `sendOobCode` endpoint to trigger email sending
- Use `"requestType": "VERIFY_EMAIL"` for verification emails
- Use `"requestType": "PASSWORD_RESET"` for password reset emails
- This requires your Firebase Web API Key (same one used in frontend config)
- Firebase will send the email using your configured email template


---

### **Step 5.3: Frontend - Email Verification Handler**

**Already handled in Step 3.4: Create Unified Auth Action Handler**

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
```javascript
// No changes needed - already updated in Step 3.6
// The /auth-action route handles both password-reset AND email-verification
```
**Note:** Routes already configured in Step 3.6. The `/auth-action` route handles both:
- Password reset (`?mode=resetPassword`)
- Email verification (`?mode=verifyEmail`)

No additional routes needed for email verification.

---


### **Step 5.5: Configure Action URL in Firebase**

- **Note:** Action URL already configured in Step 3.5. 

- Both password reset AND email verification use the same URL:
```bash
http://localhost:5173/auth-action
```

- Firebase automatically adds the correct `mode` parameter:
  - Password reset: `?mode=resetPassword&oobCode=...`
  - Email verification: `?mode=verifyEmail&oobCode=...`

- No additional configuration needed.

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
                # Resend verification email via Firebase REST API
                try:
                    FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
                    
                    if FIREBASE_WEB_API_KEY:
                        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                        payload = {
                            "requestType": "VERIFY_EMAIL",
                            "email": email
                        }
                        response = requests.post(url, json=payload)
                        
                        if response.status_code == 200:
                            logger.info(f"✅ Resent verification email to unverified user: {email}")
                        else:
                            logger.error(f"❌ Failed to resend verification email: {response.status_code}")
                    else:
                        logger.error("Firebase Web API Key not configured")
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
                
                # Send verification email via REST API
                FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

                if FIREBASE_WEB_API_KEY:
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                    payload = {
                        "requestType": "VERIFY_EMAIL",
                        "email": email
                    }
                    response = requests.post(url, json=payload)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Created Firebase user and sent verification email to: {email}")
                    else:
                        logger.error(f"❌ Failed to send verification email")
                else:
                    logger.error("Firebase Web API Key not configured")
                
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
                    # Send verification email via REST API
                    FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

                    if FIREBASE_WEB_API_KEY:
                        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                        payload = {
                            "requestType": "VERIFY_EMAIL",
                            "email": email
                        }
                        response = requests.post(url, json=payload)
                        
                        if response.status_code == 200:
                            logger.info(f"✅ Created Firebase user and sent verification email to: {email}")
                        else:
                            logger.error(f"❌ Failed to send verification email")
                    else:
                        logger.error("Firebase Web API Key not configured")

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
                
                # Send verification email via REST API
                FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

                if FIREBASE_WEB_API_KEY:
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                    payload = {
                        "requestType": "VERIFY_EMAIL",
                        "email": email
                    }
                    response = requests.post(url, json=payload)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Created Firebase user and sent verification email to: {email}")
                    else:
                        logger.error(f"❌ Failed to send verification email")
                else:
                    logger.error("Firebase Web API Key not configured")
                
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
        
        # Send verification email via Firebase REST API
        FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

        if not FIREBASE_WEB_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service not configured"
            )

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "requestType": "VERIFY_EMAIL",
            "email": email
        }

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            logger.info(f"✅ Verification email sent to {email}")
            return {"message": "Verification email sent!"}
        else:
            logger.error(f"❌ Failed to send verification email: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
                
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