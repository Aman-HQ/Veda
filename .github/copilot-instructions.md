# Copilot Instructions for Veda Backend Project

## CRITICAL: Server Management Rules

**NEVER run the backend server and test commands in the same terminal**

### Why?
- `uvicorn app.main:app --reload` runs in the foreground and blocks the terminal
- Running another command in the same terminal stops the server
- This creates an infinite loop of server start → stop → restart

### Required Workflow:

#### When Testing APIs:
1. **Terminal 1 (Server)**: 
```bash
   cd D:\chatbot\Veda\backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
   ⚠️ **Leave this terminal running. Do NOT use it for other commands.**

2. **Terminal 2 (Tests)**:
```bash
   # Now run all your test commands here ,e.g.:
   pytest tests/
   curl http://localhost:8000/metrics

   python test.py
```
   ⚠️ **Do NOT use Terminal 1 for tests or other commands.**

#### Before Starting Server:
- Always check if server is already running: `curl http://localhost:8000/health` (or any endpoint)
- If it responds, server is running → skip server startup
- If it fails, then start server in new terminal

### Copilot Instructions Configuration:
```json
"github.copilot.chat.codeGeneration.instructions": [
        {
            "text": "PROJECT RULE: For this FastAPI backend project, NEVER run 'uvicorn app.main:app' and curl/test commands in the same terminal. Uvicorn blocks the terminal. Always use separate terminals or background processes."
        },
        {
            "text": "Testing workflow: 1) Start uvicorn server in Terminal 1 and leave it running. 2) Open Terminal 2 for all curl commands and pytest tests. 3) Check if server is running on port 8000 before starting a new instance."
        },
        {
            "text": "Example correct usage: In Terminal 1, run 'uvicorn app.main:app --reload'. In Terminal 2, run 'curl http://localhost:8000/metrics' or 'pytest tests/'."
        }
    ]
```

### Never Do This:
```bash
# ❌ WRONG - Don't do this!
uvicorn app.main:app --reload && curl http://localhost:8000/metrics
```
The `curl` command will never execute because uvicorn blocks!

### Additional Notes:
- Always keep server and test commands in separate terminals or processes.

#### Alternative Approaches:
- Use background processes: `Start-Process` on Windows
- Use process managers: `pm2` or `concurrently`
- Create test scripts that manage server lifecycle