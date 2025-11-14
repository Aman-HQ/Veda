"""
Test script to verify moderation flow through the chat system
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import get_db
from app.services.chat_manager import ChatManager
from app.crud.conversation import ConversationCRUD
from app.crud.user import UserCRUD

async def test_moderation_flow():
    print("=" * 70)
    print("TESTING MODERATION FLOW THROUGH CHAT MANAGER")
    print("=" * 70)
    
    # Get a database session
    async for db in get_db():
        try:
            # Get a test user
            user = await UserCRUD.get_by_email(db, "user@test.com")
            if not user:
                print("❌ Test user not found. Please create a user first.")
                return
            
            print(f"\n✓ Test user: {user.email} (ID: {user.id})")
            
            # Get or create a conversation
            convs = await ConversationCRUD.get_user_conversations(db, str(user.id))
            if convs:
                conversation = convs[0]
                print(f"✓ Using existing conversation: {conversation.id}")
            else:
                print("❌ No conversations found. Please create one first.")
                return
            
            # Test messages
            test_cases = [
                ("suicide", "Should be BLOCKED (HIGH severity)"),
                ("I have chest pain", "Should be FLAGGED (MEDICAL_EMERGENCY)"),
                ("Where can I buy cocaine?", "Should be FLAGGED (MEDIUM)"),
                ("hello", "Should be ALLOWED (no keywords)")
            ]
            
            chat_manager = ChatManager(db)
            
            for content, expected in test_cases:
                print(f"\n{'='*70}")
                print(f"Test: '{content}'")
                print(f"Expected: {expected}")
                print(f"{'='*70}")
                
                # Send message
                result = await chat_manager.handle_user_message(
                    conversation_id=str(conversation.id),
                    user_id=str(user.id),
                    text=content
                )
                
                # Check the stored message
                from app.crud.message import MessageCRUD
                messages = await MessageCRUD.get_conversation_messages(
                    db, str(conversation.id), str(user.id)
                )
                
                # Find the user message we just sent
                user_msg = next((m for m in messages if m.sender == "user" and m.content == content), None)
                
                if user_msg:
                    print(f"\n✓ Message stored in database:")
                    print(f"  ├─ ID: {user_msg.id}")
                    print(f"  ├─ Status: {user_msg.status}")
                    print(f"  ├─ Content: {user_msg.content}")
                    print(f"  └─ Metadata: {user_msg.message_metadata}")
                    
                    # Verify status
                    if "suicide" in content.lower():
                        if user_msg.status == "blocked":
                            print("✅ PASSED: Message correctly blocked")
                        else:
                            print(f"❌ FAILED: Expected 'blocked', got '{user_msg.status}'")
                    elif "chest pain" in content.lower() or "cocaine" in content.lower():
                        if user_msg.status == "flagged":
                            print("✅ PASSED: Message correctly flagged")
                        else:
                            print(f"❌ FAILED: Expected 'flagged', got '{user_msg.status}'")
                    else:
                        if user_msg.status == "sent":
                            print("✅ PASSED: Message correctly allowed")
                        else:
                            print(f"❌ FAILED: Expected 'sent', got '{user_msg.status}'")
                else:
                    print("❌ FAILED: Message not found in database!")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
            
            print(f"\n{'='*70}")
            print("TEST COMPLETE")
            print(f"{'='*70}")
            
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_moderation_flow())
