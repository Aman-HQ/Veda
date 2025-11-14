import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import get_db
from sqlalchemy import text

async def check_messages():
    async for db in get_db():
        result = await db.execute(
            text("SELECT sender, content, status, message_metadata FROM messages ORDER BY created_at DESC LIMIT 10")
        )
        rows = result.fetchall()
        
        print("\n" + "="*120)
        print("RECENT MESSAGES IN DATABASE")
        print("="*120)
        print(f"{'Sender':<12} | {'Status':<10} | {'Content':<45} | Metadata")
        print("-"*120)
        
        for row in rows:
            metadata = str(row[3])[:50] if row[3] else "None"
            print(f"{row[0]:<12} | {row[2]:<10} | {row[1][:45]:<45} | {metadata}")
        
        await db.close()
        break

if __name__ == "__main__":
    asyncio.run(check_messages())
