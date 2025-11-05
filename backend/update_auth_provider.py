"""
It's a one-time file required: It was only used once to update existing users' auth_provider from NULL to 'email'.


you can delete it after running it once.

Scenario:
Update existing users' auth_provider based on whether they have a password
- Users WITH hashed_password → auth_provider = 'email'
- Users WITHOUT hashed_password (NULL) → auth_provider = 'google'
"""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def update_existing_users():
    """Update auth_provider for existing users"""
    async with AsyncSessionLocal() as session:
        # First, show what we're about to update
        result = await session.execute(
            text("""
                SELECT email, 
                       CASE WHEN hashed_password IS NULL THEN 'NULL' ELSE 'EXISTS' END as password_status,
                       auth_provider
                FROM users 
                WHERE auth_provider IS NULL
                ORDER BY created_at DESC
            """)
        )
        users_to_update = result.fetchall()
        
        if not users_to_update:
            print("\n✅ No users need updating - all have auth_provider set!")
            return
        
        print("\n" + "="*70)
        print("Users That Need Updating:")
        print("="*70)
        for user in users_to_update:
            email, password_status, auth_provider = user
            provider = "google" if password_status == "NULL" else "email"
            emoji = "🔵" if provider == "google" else "📧"
            print(f"{emoji} {email:<40} → Will set to: {provider}")
        
        print("="*70)
        
        # Ask for confirmation
        confirm = input("\nProceed with update? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Update cancelled")
            return
        
        # Update users based on password status
        # Users with password → email
        result = await session.execute(
            text("""
                UPDATE users 
                SET auth_provider = 'email'
                WHERE auth_provider IS NULL 
                AND hashed_password IS NOT NULL
            """)
        )
        email_users_updated = result.rowcount
        
        # Users without password → google
        result = await session.execute(
            text("""
                UPDATE users 
                SET auth_provider = 'google'
                WHERE auth_provider IS NULL 
                AND hashed_password IS NULL
            """)
        )
        google_users_updated = result.rowcount
        
        await session.commit()
        
        print("\n✅ Update Complete!")
        print(f"📧 Email users updated: {email_users_updated}")
        print(f"🔵 Google users updated: {google_users_updated}")
        print(f"Total updated: {email_users_updated + google_users_updated}\n")

if __name__ == "__main__":
    asyncio.run(update_existing_users())
