"""
Test moderation status persistence fix.
Tests that messages are properly stored with "blocked" and "flagged" status.
"""

import asyncio
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import MessageCreate
from app.crud.message import MessageCRUD
from app.services.moderation import moderate_content


async def test_moderation_crud():
    """Test that CRUD methods accept and persist status parameter."""
    print("\n" + "="*60)
    print("TEST 1: MessageCRUD status parameter")
    print("="*60)
    
    # Get database session
    async for db in get_db():
        try:
            # Get a test user
            result = await db.execute(select(User).limit(1))
            test_user = result.scalars().first()
            
            if not test_user:
                print("❌ No test user found. Please create a user first.")
                return
            
            print(f"✓ Using test user: {test_user.email}")
            
            # Get or create a test conversation
            result = await db.execute(
                select(Conversation)
                .where(Conversation.user_id == test_user.id)
                .limit(1)
            )
            conversation = result.scalars().first()
            
            if not conversation:
                print("❌ No conversation found. Please create a conversation first.")
                return
            
            print(f"✓ Using conversation: {conversation.id}")
            
            # Test 1: Create message with "blocked" status
            print("\n--- Test 1a: Create message with 'blocked' status ---")
            blocked_msg = MessageCreate(
                content="I want to hurt myself",
                message_metadata={"test": "blocked"}
            )
            
            blocked_message = await MessageCRUD.create(
                db=db,
                message_create=blocked_msg,
                conversation_id=conversation.id,
                sender="user",
                status="blocked"
            )
            
            print(f"✓ Message created with ID: {blocked_message.id}")
            print(f"  Status: {blocked_message.status}")
            print(f"  Content: {blocked_message.content[:50]}...")
            
            if blocked_message.status == "blocked":
                print("✅ PASSED: Message stored with 'blocked' status")
            else:
                print(f"❌ FAILED: Expected 'blocked', got '{blocked_message.status}'")
            
            # Test 2: Create message with "flagged" status
            print("\n--- Test 1b: Create message with 'flagged' status ---")
            flagged_msg = MessageCreate(
                content="I want to buy some cocaine",
                message_metadata={"test": "flagged"}
            )
            
            flagged_message = await MessageCRUD.create_with_count_increment(
                db=db,
                conversation_id=conversation.id,
                sender="user",
                status="flagged",
                message_create=flagged_msg
            )
            
            print(f"✓ Message created with ID: {flagged_message.id}")
            print(f"  Status: {flagged_message.status}")
            print(f"  Content: {flagged_message.content[:50]}...")
            
            if flagged_message.status == "flagged":
                print("✅ PASSED: Message stored with 'flagged' status")
            else:
                print(f"❌ FAILED: Expected 'flagged', got '{flagged_message.status}'")
            
            # Cleanup
            await db.delete(blocked_message)
            await db.delete(flagged_message)
            await db.commit()
            
            print("\n✓ Test messages cleaned up")
            
        finally:
            await db.close()
            break


async def test_moderation_service():
    """Test that moderation service returns correct actions."""
    print("\n" + "="*60)
    print("TEST 2: Moderation Service")
    print("="*60)
    
    # Test HIGH severity (block)
    print("\n--- Test 2a: HIGH severity (suicide keyword) ---")
    result = moderate_content(
        "I want to commit suicide",
        context={"test": "high"}
    )
    print(f"  Action: {result.action}")
    print(f"  Severity: {result.severity}")
    print(f"  Is Safe: {result.is_safe}")
    print(f"  Keywords: {result.matched_keywords}")
    
    if result.action == "block" and not result.is_safe:
        print("✅ PASSED: HIGH severity returns 'block' action")
    else:
        print(f"❌ FAILED: Expected action='block', is_safe=False")
    
    # Test MEDIUM severity (flag)
    print("\n--- Test 2b: MEDIUM severity (drugs keyword) ---")
    result = moderate_content(
        "Where can I buy cocaine?",
        context={"test": "medium"}
    )
    print(f"  Action: {result.action}")
    print(f"  Severity: {result.severity}")
    print(f"  Is Safe: {result.is_safe}")
    print(f"  Keywords: {result.matched_keywords}")
    
    if result.action == "flag" and result.is_safe:
        print("✅ PASSED: MEDIUM severity returns 'flag' action")
    else:
        print(f"❌ FAILED: Expected action='flag', is_safe=True")
    
    # Test MEDICAL_EMERGENCY severity (flag)
    print("\n--- Test 2c: MEDICAL_EMERGENCY severity ---")
    result = moderate_content(
        "I'm having severe chest pain right now",
        context={"test": "emergency"}
    )
    print(f"  Action: {result.action}")
    print(f"  Severity: {result.severity}")
    print(f"  Is Safe: {result.is_safe}")
    print(f"  Keywords: {result.matched_keywords}")
    
    if result.action == "flag" and result.is_safe:
        print("✅ PASSED: MEDICAL_EMERGENCY returns 'flag' action")
    else:
        print(f"❌ FAILED: Expected action='flag', is_safe=True")
    
    # Test LOW severity (allow)
    print("\n--- Test 2d: LOW severity (mild language) ---")
    result = moderate_content(
        "This is stupid and annoying",
        context={"test": "low"}
    )
    print(f"  Action: {result.action}")
    print(f"  Severity: {result.severity}")
    print(f"  Is Safe: {result.is_safe}")
    print(f"  Keywords: {result.matched_keywords}")
    
    if result.action == "allow" and result.is_safe:
        print("✅ PASSED: LOW severity returns 'allow' action")
    else:
        print(f"❌ FAILED: Expected action='allow', is_safe=True")


async def test_database_persistence():
    """Test that moderation status is persisted in database."""
    print("\n" + "="*60)
    print("TEST 3: Database Persistence")
    print("="*60)
    
    async for db in get_db():
        try:
            # Get test conversation
            result = await db.execute(
                select(Conversation).limit(1)
            )
            conversation = result.scalars().first()
            
            if not conversation:
                print("❌ No conversation found")
                return
            
            # Create messages with different statuses
            test_messages = []
            
            # Blocked message
            blocked = MessageCreate(
                content="Test blocked message",
                message_metadata={"moderation": {"action": "block", "severity": "HIGH"}}
            )
            msg1 = await MessageCRUD.create(
                db=db, 
                message_create=blocked,
                conversation_id=conversation.id,
                sender="user",
                status="blocked"
            )
            test_messages.append(msg1)
            print(f"✓ Created blocked message: {msg1.id}")
            
            # Flagged message
            flagged = MessageCreate(
                content="Test flagged message",
                message_metadata={"moderation": {"action": "flag", "severity": "MEDIUM"}}
            )
            msg2 = await MessageCRUD.create(
                db=db,
                message_create=flagged,
                conversation_id=conversation.id,
                sender="user",
                status="flagged"
            )
            test_messages.append(msg2)
            print(f"✓ Created flagged message: {msg2.id}")
            
            # Sent message
            sent = MessageCreate(
                content="Test normal message",
                message_metadata={}
            )
            msg3 = await MessageCRUD.create(
                db=db,
                message_create=sent,
                conversation_id=conversation.id,
                sender="user",
                status="sent"
            )
            test_messages.append(msg3)
            print(f"✓ Created sent message: {msg3.id}")
            
            # Query back from database
            print("\n--- Verifying database persistence ---")
            result = await db.execute(
                select(Message).where(
                    Message.id.in_([msg.id for msg in test_messages])
                )
            )
            db_messages = result.scalars().all()
            
            status_map = {msg.id: msg.status for msg in db_messages}
            
            passed = True
            for msg in test_messages:
                db_status = status_map.get(msg.id)
                if db_status == msg.status:
                    print(f"✅ Message {msg.id}: status='{msg.status}' (persisted correctly)")
                else:
                    print(f"❌ Message {msg.id}: expected '{msg.status}', got '{db_status}'")
                    passed = False
            
            if passed:
                print("\n✅ ALL PASSED: All statuses persisted correctly")
            else:
                print("\n❌ SOME FAILED: Some statuses not persisted")
            
            # Cleanup
            for msg in test_messages:
                await db.delete(msg)
            await db.commit()
            print("\n✓ Test messages cleaned up")
            
        finally:
            await db.close()
            break


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MODERATION FIX VERIFICATION TESTS")
    print("="*60)
    
    try:
        await test_moderation_service()
        await test_moderation_crud()
        await test_database_persistence()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
