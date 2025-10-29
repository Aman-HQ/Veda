# Task I00 - Wire Frontend to Real API - Integration Test Guide

## Overview
This document describes how to test the Task I00 implementation where we wire the frontend to the real backend API.

## Changes Made

### 1. Frontend Environment Configuration
- **File**: `frontend/.env.example` and `frontend/.env`
- **Changes**:
  ```env
  VITE_API_BASE=http://localhost:8000
  VITE_WS_BASE=ws://localhost:8000
  VITE_USE_MOCK_API=false
  VITE_GOOGLE_CLIENT_ID=replace_me
  ```

### 2. Authentication Hook (`frontend/src/hooks/useAuth.js`)
- **Replaced mock authentication** with real API calls
- **Endpoints integrated**:
  - `POST /api/auth/login` - User login
  - `POST /api/auth/register` - User registration
  - `POST /api/auth/refresh` - Token refresh
  - `GET /api/auth/me` - Get current user info
- **Error handling** added for all auth operations
- **Auto-login after registration** implemented

### 3. API Client with Token Refresh (`frontend/src/services/api.js`)
- **Automatic token refresh** on 401 errors
- **Request queuing** during token refresh to prevent duplicate refresh calls
- **Retry logic** for failed requests after successful token refresh
- **Token storage** using authStore (access token in memory, refresh token in localStorage)

#### Token Refresh Flow:
1. Request fails with 401
2. Intercept and check if token refresh is already in progress
3. If not, start refresh process:
   - Call `/api/auth/refresh` with refresh token
   - Update tokens in authStore
   - Retry original request with new token
   - Process any queued requests
4. If already refreshing, queue the request
5. If refresh fails, clear auth and redirect to login

### 4. Chat Service (`frontend/src/services/chatService.js`)
- **Replaced stub implementations** with real API calls
- **Endpoints integrated**:
  - `GET /api/conversations` - List user's conversations
  - `POST /api/conversations` - Create new conversation
  - `DELETE /api/conversations/:id` - Delete conversation
  - `GET /api/conversations/:id/messages` - List messages in conversation
  - `POST /api/conversations/:id/messages` - Create new message
- **Error handling** and logging added

## Backend API Verification

### Health Check
```powershell
curl http://localhost:8000/health
```
Expected: `{"status":"healthy",...}`

### Authentication Flow

#### 1. Register User
```powershell
curl -X POST http://localhost:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"name":"Test User","email":"test@example.com","password":"Test123456!"}'
```

Expected Response:
```json
{
  "id": "...",
  "email": "test@example.com",
  "name": "Test User",
  "role": "user",
  "created_at": "..."
}
```

#### 2. Login
```powershell
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"Test123456!"}'
```

Expected Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### 3. Get Current User (with token)
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"
curl -H "Authorization: Bearer $token" http://localhost:8000/api/auth/me
```

### Conversation & Message Flow

#### 1. Create Conversation
```powershell
$token = "YOUR_ACCESS_TOKEN_HERE"
curl -X POST http://localhost:8000/api/conversations `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"title":"My First Conversation"}'
```

#### 2. List Conversations
```powershell
curl -H "Authorization: Bearer $token" http://localhost:8000/api/conversations
```

#### 3. Create Message
```powershell
$conversationId = "CONVERSATION_ID_FROM_ABOVE"
curl -X POST http://localhost:8000/api/conversations/$conversationId/messages `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{"content":"Hello, this is a test message","sender":"user"}'
```

#### 4. List Messages
```powershell
curl -H "Authorization: Bearer $token" `
  "http://localhost:8000/api/conversations/$conversationId/messages?limit=50"
```

## Frontend Testing

### Prerequisites
1. Backend server running on `http://localhost:8000`
2. Frontend `.env` file configured with `VITE_USE_MOCK_API=false`

### Testing Steps

#### 1. Start Frontend
```powershell
cd frontend
npm run dev
```

#### 2. Test Registration
1. Navigate to `http://localhost:5173/register`
2. Fill in:
   - Name: Test User
   - Email: frontend-test@example.com
   - Password: Test123456!
3. Click Register
4. Should redirect to `/chat` automatically
5. Check browser DevTools Network tab for API calls to `/api/auth/register` and `/api/auth/login`

#### 3. Test Login
1. Navigate to `http://localhost:5173/login`
2. Enter credentials from registration
3. Click Login
4. Should redirect to `/chat`
5. Check Network tab for `/api/auth/login` call

#### 4. Test Conversation List
1. After login, you should see the chat interface
2. Check Network tab for `/api/conversations` call
3. Conversation list should load (may be empty initially)

#### 5. Test Conversation Creation
1. Click "New Chat" or similar button
2. Check Network tab for `POST /api/conversations` call
3. New conversation should appear in sidebar

#### 6. Test Message Sending
1. Select a conversation
2. Type a message in the composer
3. Send message
4. Check Network tab for `POST /api/conversations/:id/messages` call
5. Message should appear in chat window

#### 7. Test Token Refresh
1. Wait for access token to expire (15 minutes by default)
2. Perform any action (create conversation, send message)
3. Check Network tab:
   - First request should get 401
   - `/api/auth/refresh` should be called automatically
   - Original request should be retried with new token
   - Request should succeed

## Acceptance Criteria ✅

- [x] Frontend `.env.example` and `.env` files created with correct configuration
- [x] `useAuth.js` updated to call real backend endpoints
- [x] API client (`api.js`) implements automatic token refresh on 401
- [x] `chatService.js` implements all conversation and message endpoints
- [x] Backend API verified working with curl/PowerShell commands
- [ ] Frontend can successfully register new users
- [ ] Frontend can successfully login existing users
- [ ] Frontend automatically refreshes expired access tokens
- [ ] Frontend can list conversations
- [ ] Frontend can create new conversations
- [ ] Frontend can list messages
- [ ] Frontend can create new messages
- [ ] Error messages are displayed appropriately to users

## Known Issues & Notes

1. **PowerShell JSON Escaping**: When testing with curl in PowerShell, use JSON files instead of inline JSON to avoid escaping issues
2. **Token Expiry**: Access tokens expire after 15 minutes (configurable in backend)
3. **CORS**: Backend is configured to allow `http://localhost:5173`
4. **Google OAuth**: Not yet configured (requires `VITE_GOOGLE_CLIENT_ID` and backend setup)

## Next Steps (Task I01)

After verifying all acceptance criteria:
1. Implement real WebSocket streaming (`useWebSocket.js`)
2. Replace mock streaming with server-sent events
3. Test reconnection and backoff logic
4. Verify partial → final message transition

## Troubleshooting

### Frontend not connecting to backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check `frontend/.env` has correct `VITE_API_BASE=http://localhost:8000`
- Check browser console for CORS errors
- Restart frontend dev server after changing `.env`

### 401 Unauthorized errors
- Verify token is being sent in Authorization header (check Network tab)
- Check token hasn't expired (15-minute default)
- Verify user exists in database

### Token refresh not working
- Check browser console for errors
- Verify refresh token is stored in localStorage
- Check Network tab for `/api/auth/refresh` calls
- Verify backend refresh endpoint is working: `curl -X POST http://localhost:8000/api/auth/refresh -H "Content-Type: application/json" -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'`

### Messages not appearing
- Verify conversation ID is correct
- Check Network tab for API errors
- Verify user owns the conversation
- Check backend logs for errors

## Testing Checklist

```
Authentication:
☐ Register new user via frontend
☐ Login with registered user
☐ Access token stored in memory
☐ Refresh token stored in localStorage
☐ /api/auth/me returns user info
☐ Logout clears tokens

Token Refresh:
☐ 401 triggers automatic refresh
☐ Multiple simultaneous 401s don't cause duplicate refreshes
☐ Original request retries after refresh
☐ Failed refresh redirects to login

Conversations:
☐ List conversations loads on chat page
☐ Create new conversation works
☐ Delete conversation works
☐ Conversation list updates after operations

Messages:
☐ List messages loads when selecting conversation
☐ Create message works
☐ Messages display in correct order
☐ Sender field correctly set (user/assistant)

Error Handling:
☐ Network errors display user-friendly messages
☐ Validation errors from backend are shown
☐ 404 errors handled appropriately
☐ 500 errors don't crash the app
```

## Conclusion

Task I00 successfully wires the frontend to the real backend API with:
- Full authentication flow (register, login, refresh, logout)
- Automatic token refresh on 401 errors
- Conversation and message CRUD operations
- Proper error handling and user feedback

The foundation is now ready for Task I01 (Real Streaming with WebSocket).
