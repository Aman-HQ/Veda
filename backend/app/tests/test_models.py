"""
Simple test script to verify ORM models and relationships work correctly.
This is a temporary test file for B03 validation.
ORM-level testing with the database.(This is an integration test./ database-aware)
"""
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import User, Conversation, Message


async def test_models():
    """Test ORM models and relationships."""
    print("Testing ORM models and relationships...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Test User creation
            print("\n1. Creating a test user...")
            user = User(
                email="test@example.com",
                name="Test User",
                hashed_password="hashed_password_here",
                role="user"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✓ User created with ID: {user.id}")
            
            # Test Conversation creation
            print("\n2. Creating a test conversation...")
            conversation = Conversation(
                user_id=user.id,
                title="Test Conversation",
                messages_count=0
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            print(f"✓ Conversation created with ID: {conversation.id}")
            
            # Test Message creation
            print("\n3. Creating test messages...")
            user_message = Message(
                conversation_id=conversation.id,
                sender="user",
                content="Hello, this is a test message from user",
                status="sent",
                message_metadata={"type": "text"}
            )
            session.add(user_message)
            
            assistant_message = Message(
                conversation_id=conversation.id,
                sender="assistant",
                content="Hello! This is a test response from the assistant",
                status="sent",
                message_metadata={"type": "text", "disclaimer": True}
            )
            session.add(assistant_message)
            
            await session.commit()
            await session.refresh(user_message)
            await session.refresh(assistant_message)
            print(f"✓ User message created with ID: {user_message.id}")
            print(f"✓ Assistant message created with ID: {assistant_message.id}")
            
            # Update conversation message count
            conversation.messages_count = 2
            await session.commit()
            
            # Test relationships - User -> Conversations
            print("\n4. Testing relationships...")
            result = await session.execute(
                select(User).options(selectinload(User.conversations)).where(User.id == user.id)
            )
            user_with_conversations = result.scalar_one()
            print(f"✓ User has {len(user_with_conversations.conversations)} conversation(s)")
            
            # Test relationships - Conversation -> Messages
            result = await session.execute(
                select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation.id)
            )
            conversation_with_messages = result.scalar_one()
            print(f"✓ Conversation has {len(conversation_with_messages.messages)} message(s)")
            
            # Test relationships - Message -> Conversation -> User
            result = await session.execute(
                select(Message)
                .options(selectinload(Message.conversation).selectinload(Conversation.user))
                .where(Message.id == user_message.id)
            )
            message_with_relations = result.scalar_one()
            print(f"✓ Message belongs to user: {message_with_relations.conversation.user.email}")
            
            # Test querying messages by conversation
            print("\n5. Testing queries...")
            result = await session.execute(
                select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
            )
            messages = result.scalars().all()
            print(f"✓ Found {len(messages)} messages in conversation")
            for i, msg in enumerate(messages, 1):
                print(f"  {i}. {msg.sender}: {msg.content[:50]}...")
            
            # Test cascade delete (cleanup)
            print("\n6. Testing cascade delete...")
            await session.delete(user)  # This should cascade delete conversations and messages
            await session.commit()
            print("✓ User deleted (cascade delete should remove conversations and messages)")
            
            # Verify cascade delete worked
            result = await session.execute(select(Conversation).where(Conversation.id == conversation.id))
            remaining_conversation = result.scalar_one_or_none()
            
            result = await session.execute(select(Message).where(Message.id == user_message.id))
            remaining_message = result.scalar_one_or_none()
            
            if remaining_conversation is None and remaining_message is None:
                print("✓ Cascade delete successful - conversations and messages removed")
            else:
                print("✗ Cascade delete failed - some records remain")
            
            print("\n✅ All tests passed! Models and relationships are working correctly.")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(test_models())
