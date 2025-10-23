"""
Simple model validation test - just check that models can be imported and instantiated.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_model_imports():
    """Test that all models can be imported without circular import errors."""
    try:
        print("Testing model imports...")
        
        # Test individual model imports
        from app.models.user import User
        print("+ User model imported successfully")
        
        from app.models.conversation import Conversation
        print("+ Conversation model imported successfully")
        
        from app.models.message import Message
        print("+ Message model imported successfully")
        
        # Test schema imports
        from app.schemas.auth import User as UserSchema, LoginRequest
        print("+ Auth schemas imported successfully")
        
        from app.schemas.chat import Message as MessageSchema, Conversation as ConversationSchema
        print("+ Chat schemas imported successfully")
        
        print("\n[SUCCESS] All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        return False

def test_model_structure():
    """Test that models have the expected attributes."""
    try:
        print("\nTesting model structure...")
        
        from app.models.user import User
        from app.models.conversation import Conversation
        from app.models.message import Message
        
        # Check User model attributes
        user_attrs = ['id', 'email', 'hashed_password', 'name', 'role', 'refresh_tokens', 'created_at']
        for attr in user_attrs:
            assert hasattr(User, attr), f"User missing attribute: {attr}"
        print("+ User model has all required attributes")
        
        # Check Conversation model attributes
        conv_attrs = ['id', 'user_id', 'title', 'messages_count', 'created_at']
        for attr in conv_attrs:
            assert hasattr(Conversation, attr), f"Conversation missing attribute: {attr}"
        print("+ Conversation model has all required attributes")
        
        # Check Message model attributes
        msg_attrs = ['id', 'conversation_id', 'sender', 'content', 'status', 'message_metadata', 'created_at']
        for attr in msg_attrs:
            assert hasattr(Message, attr), f"Message missing attribute: {attr}"
        print("+ Message model has all required attributes")
        
        print("\n[SUCCESS] All model structures are correct!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Structure test failed: {e}")
        return False

def test_schema_validation():
    """Test that Pydantic schemas work correctly."""
    try:
        print("\nTesting schema validation...")
        
        from app.schemas.auth import UserCreate, LoginRequest
        from app.schemas.chat import MessageCreate, ConversationCreate
        
        # Test UserCreate schema
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User"
        }
        user_schema = UserCreate(**user_data)
        assert user_schema.email == "test@example.com"
        print("+ UserCreate schema validation works")
        
        # Test LoginRequest schema
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        login_schema = LoginRequest(**login_data)
        assert login_schema.email == "test@example.com"
        print("+ LoginRequest schema validation works")
        
        # Test MessageCreate schema
        message_data = {
            "content": "Hello, this is a test message",
            "type": "text"
        }
        message_schema = MessageCreate(**message_data)
        assert message_schema.content == "Hello, this is a test message"
        print("+ MessageCreate schema validation works")
        
        # Test ConversationCreate schema
        conv_data = {
            "title": "Test Conversation"
        }
        conv_schema = ConversationCreate(**conv_data)
        assert conv_schema.title == "Test Conversation"
        print("+ ConversationCreate schema validation works")
        
        print("\n[SUCCESS] All schema validations work correctly!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Schema validation failed: {e}")
        return False

if __name__ == "__main__":
    print("=== B03 Model and Schema Validation Test ===\n")
    
    success = True
    success &= test_model_imports()
    success &= test_model_structure()
    success &= test_schema_validation()
    
    if success:
        print("\n[SUCCESS] All tests passed! B03 implementation is working correctly.")
    else:
        print("\n[FAILED] Some tests failed. Please check the implementation.")
        sys.exit(1)
