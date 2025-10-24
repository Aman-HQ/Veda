#!/usr/bin/env python3

import traceback

try:
    from app.main import app
    print("✅ FastAPI app imports successfully with B08 moderation")
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
