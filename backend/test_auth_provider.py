"""
Quick test script to verify auth_provider is set correctly
"""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def check_auth_providers():
    """Check auth_provider values in database"""
    async with AsyncSessionLocal() as session:
        # Get all users with their auth_provider
        result = await session.execute(
            text("SELECT email, auth_provider FROM users ORDER BY created_at DESC")
        )
        users = result.fetchall()
        
        print("\n" + "="*60)
        print("Current Users in Database:")
        print("="*60)
        
        if not users:
            print("No users found in database")
        else:
            for user in users:
                email, auth_provider = user
                emoji = "📧" if auth_provider == "email" else "🔵" if auth_provider == "google" else "❓"
                print(f"{emoji} {email:<40} → {auth_provider}")
        
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(check_auth_providers())
