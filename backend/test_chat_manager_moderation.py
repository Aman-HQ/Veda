"""
Simple test to verify ChatManager integration with moderation.
"""

import asyncio
from uuid import UUID

from app.db.session import get_db
from app.models.conversation import Conversation
from app.services.chat_manager import ChatManager


async def test_chat_manager_moderation():
    """Test that ChatManager properly handles moderation."""
    print("\n" + "="*60)
    print("CHAT MANAGER MODERATION TEST")
    print("="*60)
    
    async for db in get_db():
        try:
            # Get test conversation
            result = await db.execute(
                "SELECT id, user_id FROM conversations LIMIT 1"
            )
            row = result.first()
            
            if not row:
                print("❌ No conversation found")
                return
            
            conversation_id = str(row[0])
            user_id = str(row[1])
            
            print(f"✓ Using conversation: {conversation_id}")
            print(f"✓ User: {user_id}")
            
            # Create chat manager
            chat_manager = ChatManager(db)
            
            # Test 1: Blocked message
            print("\n--- Test 1: HIGH severity (blocked) ---")
            try:
                result = await chat_manager.handle_user_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    text="I want to commit suicide",
                    client_message_id="test-blocked-1"
                )
                
                if result.get("blocked"):
                    print("✅ Message blocked successfully")
                    print(f"   User message ID: {result.get('user_message_id')}")
                    print(f"   Assistant response: {result.get('response')[:100]}...")
                    
                    # Verify message was stored as "blocked"
                    msg_id = result.get('user_message_id')
                    if msg_id:
                        from app.models.message import Message
                        from sqlalchemy import select
                        
                        db_result = await db.execute(
                            select(Message).where(Message.id == UUID(msg_id))
                        )
                        message = db_result.scalars().first()
                        
                        if message and message.status == "blocked":
                            print("✅ Message status correctly stored as 'blocked'")
                        else:
                            print(f"❌ Message status is '{message.status if message else 'NOT FOUND'}'")
                else:
                    print("❌ Message was not blocked")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Test 2: Flagged message
            print("\n--- Test 2: MEDIUM severity (flagged) ---")
            try:
                result = await chat_manager.handle_user_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    text="Where can I buy cocaine?",
                    client_message_id="test-flagged-1"
                )
                
                if not result.get("blocked"):
                    print("✅ Message allowed (not blocked)")
                    print(f"   User message ID: {result.get('user_message_id')}")
                    
                    # Verify message was stored as "flagged"
                    msg_id = result.get('user_message_id')
                    if msg_id:
                        from app.models.message import Message
                        from sqlalchemy import select
                        
                        db_result = await db.execute(
                            select(Message).where(Message.id == UUID(msg_id))
                        )
                        message = db_result.scalars().first()
                        
                        if message and message.status == "flagged":
                            print("✅ Message status correctly stored as 'flagged'")
                            print(f"   Moderation metadata: {message.message_metadata.get('moderation')}")
                        else:
                            print(f"❌ Message status is '{message.status if message else 'NOT FOUND'}'")
                else:
                    print("❌ Message was incorrectly blocked")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Test 3: Normal message
            print("\n--- Test 3: Normal message (sent) ---")
            try:
                result = await chat_manager.handle_user_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    text="What are the symptoms of diabetes?",
                    client_message_id="test-normal-1"
                )
                
                print("✅ Message processed successfully")
                print(f"   User message ID: {result.get('user_message_id')}")
                
                # Verify message was stored as "sent"
                msg_id = result.get('user_message_id')
                if msg_id:
                    from app.models.message import Message
                    from sqlalchemy import select
                    
                    db_result = await db.execute(
                        select(Message).where(Message.id == UUID(msg_id))
                    )
                    message = db_result.scalars().first()
                    
                    if message and message.status == "sent":
                        print("✅ Message status correctly stored as 'sent'")
                    else:
                        print(f"❌ Message status is '{message.status if message else 'NOT FOUND'}'")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("\n" + "="*60)
            print("TEST COMPLETED")
            print("="*60)
            
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(test_chat_manager_moderation())
