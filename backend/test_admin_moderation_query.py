"""
Test admin moderation endpoint to verify it can query flagged/blocked messages.
"""

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import MessageCreate
from app.crud.message import MessageCRUD


async def create_test_moderation_messages():
    """Create test messages with different moderation statuses."""
    print("\n" + "="*60)
    print("Creating test moderation messages...")
    print("="*60)
    
    async for db in get_db():
        try:
            # Get test user and conversation
            result = await db.execute(select(Conversation).limit(1))
            conversation = result.scalars().first()
            
            if not conversation:
                print("❌ No conversation found")
                return []
            
            test_messages = []
            
            # Create HIGH severity - blocked
            msg1 = MessageCreate(
                content="I want to commit suicide",
                message_metadata={
                    "moderation": {
                        "action": "block",
                        "severity": "HIGH",
                        "matched_keywords": ["suicide"],
                        "is_safe": False
                    }
                }
            )
            blocked = await MessageCRUD.create(
                db=db,
                message_create=msg1,
                conversation_id=conversation.id,
                sender="user",
                status="blocked"
            )
            test_messages.append(blocked)
            print(f"✓ Created BLOCKED message: {blocked.id}")
            
            # Create MEDIUM severity - flagged
            msg2 = MessageCreate(
                content="Where can I buy cocaine?",
                message_metadata={
                    "moderation": {
                        "action": "flag",
                        "severity": "MEDIUM",
                        "matched_keywords": ["cocaine"],
                        "is_safe": True
                    }
                }
            )
            flagged1 = await MessageCRUD.create(
                db=db,
                message_create=msg2,
                conversation_id=conversation.id,
                sender="user",
                status="flagged"
            )
            test_messages.append(flagged1)
            print(f"✓ Created FLAGGED message (MEDIUM): {flagged1.id}")
            
            # Create MEDICAL_EMERGENCY severity - flagged
            msg3 = MessageCreate(
                content="I'm having severe chest pain",
                message_metadata={
                    "moderation": {
                        "action": "flag",
                        "severity": "MEDICAL_EMERGENCY",
                        "matched_keywords": ["chest pain"],
                        "is_safe": True
                    }
                }
            )
            flagged2 = await MessageCRUD.create(
                db=db,
                message_create=msg3,
                conversation_id=conversation.id,
                sender="user",
                status="flagged"
            )
            test_messages.append(flagged2)
            print(f"✓ Created FLAGGED message (EMERGENCY): {flagged2.id}")
            
            # Create normal message
            msg4 = MessageCreate(
                content="What are the symptoms of diabetes?",
                message_metadata={}
            )
            normal = await MessageCRUD.create(
                db=db,
                message_create=msg4,
                conversation_id=conversation.id,
                sender="user",
                status="sent"
            )
            test_messages.append(normal)
            print(f"✓ Created SENT message: {normal.id}")
            
            return [str(msg.id) for msg in test_messages]
            
        finally:
            await db.close()
            break


async def query_moderation_messages():
    """Query messages by moderation status (simulating admin endpoint)."""
    print("\n" + "="*60)
    print("Querying messages by moderation status...")
    print("="*60)
    
    async for db in get_db():
        try:
            # Query BLOCKED messages
            print("\n--- BLOCKED Messages ---")
            result = await db.execute(
                select(Message)
                .where(Message.status == "blocked")
                .order_by(Message.created_at.desc())
                .limit(10)
            )
            blocked_msgs = result.scalars().all()
            
            print(f"Found {len(blocked_msgs)} blocked messages:")
            for msg in blocked_msgs:
                moderation = msg.message_metadata.get("moderation", {})
                print(f"  • ID: {msg.id}")
                print(f"    Content: {msg.content[:50]}...")
                print(f"    Status: {msg.status}")
                print(f"    Severity: {moderation.get('severity', 'N/A')}")
                print(f"    Keywords: {moderation.get('matched_keywords', [])}")
                print()
            
            # Query FLAGGED messages
            print("\n--- FLAGGED Messages ---")
            result = await db.execute(
                select(Message)
                .where(Message.status == "flagged")
                .order_by(Message.created_at.desc())
                .limit(10)
            )
            flagged_msgs = result.scalars().all()
            
            print(f"Found {len(flagged_msgs)} flagged messages:")
            for msg in flagged_msgs:
                moderation = msg.message_metadata.get("moderation", {})
                print(f"  • ID: {msg.id}")
                print(f"    Content: {msg.content[:50]}...")
                print(f"    Status: {msg.status}")
                print(f"    Severity: {moderation.get('severity', 'N/A')}")
                print(f"    Keywords: {moderation.get('matched_keywords', [])}")
                print()
            
            # Query all moderation stats
            print("\n--- Moderation Statistics ---")
            result = await db.execute(
                select(
                    Message.status,
                    func.count(Message.id).label('count')
                )
                .group_by(Message.status)
            )
            stats = result.all()
            
            for status, count in stats:
                print(f"  • {status}: {count} messages")
            
            # Verify test messages exist
            if len(blocked_msgs) > 0 and len(flagged_msgs) > 0:
                print("\n✅ SUCCESS: Admin can query messages by moderation status")
            else:
                print("\n⚠️  WARNING: No moderation messages found")
            
        finally:
            await db.close()
            break


async def cleanup_test_messages(message_ids):
    """Clean up test messages."""
    if not message_ids:
        return
    
    print("\n" + "="*60)
    print("Cleaning up test messages...")
    print("="*60)
    
    async for db in get_db():
        try:
            from uuid import UUID
            for msg_id in message_ids:
                result = await db.execute(
                    select(Message).where(Message.id == UUID(msg_id))
                )
                msg = result.scalars().first()
                if msg:
                    await db.delete(msg)
            
            await db.commit()
            print(f"✓ Deleted {len(message_ids)} test messages")
            
        finally:
            await db.close()
            break


async def main():
    """Run moderation query tests."""
    print("\n" + "="*60)
    print("ADMIN MODERATION QUERY TEST")
    print("="*60)
    
    try:
        # Create test messages
        message_ids = await create_test_moderation_messages()
        
        # Query messages (simulate admin endpoint)
        await query_moderation_messages()
        
        # Ask user if they want to keep the test messages
        print("\n" + "="*60)
        response = input("Keep test messages for frontend testing? (y/N): ")
        
        if response.lower() != 'y':
            await cleanup_test_messages(message_ids)
        else:
            print("✓ Test messages kept. You can view them in the admin moderation page.")
            print(f"  Message IDs: {', '.join(message_ids)}")
        
        print("\n" + "="*60)
        print("TEST COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
