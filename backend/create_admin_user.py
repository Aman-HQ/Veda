"""
Quick script to create an admin user for testing admin dashboard
Run: python create_admin_user.py
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def create_admin():
    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@veda.com")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("✅ Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
            print(f"   ID: {existing_admin.id}")
            
            # Update to admin if not already
            if existing_admin.role != "admin":
                existing_admin.role = "admin"
                await session.commit()
                print("   ✅ Updated role to admin!")
            return
        
        # Create new admin user
        admin = User(
            email="admin@veda.com",
            name="Admin User",
            hashed_password=hash_password("admin123"),
            role="admin"
        )
        
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        
        print("✅ Admin user created successfully!")
        print(f"   Email: admin@veda.com")
        print(f"   Password: admin123")
        print(f"   Role: {admin.role}")
        print(f"   ID: {admin.id}")
        print("\n📝 You can now login with these credentials and access /admin")

if __name__ == "__main__":
    asyncio.run(create_admin())
