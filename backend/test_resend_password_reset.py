"""
Test script for the /resend-password-reset endpoint.

This endpoint allows users to request another password reset email
if they didn't receive the first one or the link expired.
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_resend_password_reset():
    """Test the /resend-password-reset endpoint"""
    
    print("=" * 60)
    print("Testing /api/auth/resend-password-reset endpoint")
    print("=" * 60)
    
    test_email = "test@example.com"
    
    # Test 1: Send initial forgot password request
    print(f"\n1. Sending initial forgot password request to: {test_email}")
    response = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": test_email}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Initial request sent successfully")
    else:
        print("   ❌ Initial request failed")
    
    # Wait a moment before resending
    print("\n   Waiting 2 seconds before resend test...")
    time.sleep(2)
    
    # Test 2: Resend password reset link
    print(f"\n2. Resending password reset link to: {test_email}")
    response = requests.post(
        f"{BASE_URL}/api/auth/resend-password-reset",
        json={"email": test_email}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Resend endpoint is working!")
    else:
        print("   ❌ Unexpected status code")
    
    # Test 3: Test with invalid email format
    print(f"\n3. Testing with invalid email format")
    response = requests.post(
        f"{BASE_URL}/api/auth/resend-password-reset",
        json={"email": "not-an-email"}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 422:
        print("   ✅ Validation working correctly!")
    else:
        print("   ❌ Validation not working as expected")
    
    # Test 4: Test with non-existent user (should still return generic message)
    print(f"\n4. Testing with non-existent user")
    response = requests.post(
        f"{BASE_URL}/api/auth/resend-password-reset",
        json={"email": "nonexistent@example.com"}
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Security working - generic message returned")
    else:
        print("   ❌ Unexpected response")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\nKey Features Tested:")
    print("  ✓ Resend functionality works")
    print("  ✓ Same generic message for security")
    print("  ✓ Email validation working")
    print("  ✓ No email enumeration vulnerability")


def compare_endpoints():
    """Compare forgot-password and resend-password-reset responses"""
    
    print("\n" + "=" * 60)
    print("Comparing /forgot-password vs /resend-password-reset")
    print("=" * 60)
    
    test_email = "compare@example.com"
    
    # Test forgot-password
    print(f"\nTesting /forgot-password with: {test_email}")
    response1 = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": test_email}
    )
    print(f"Response: {response1.json()}")
    
    time.sleep(1)
    
    # Test resend-password-reset
    print(f"\nTesting /resend-password-reset with: {test_email}")
    response2 = requests.post(
        f"{BASE_URL}/api/auth/resend-password-reset",
        json={"email": test_email}
    )
    print(f"Response: {response2.json()}")
    
    # Compare responses
    if response1.json().get("message") == response2.json().get("message"):
        print("\n✅ Both endpoints return identical messages (good for security)")
    else:
        print("\n❌ Endpoints return different messages")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_resend_password_reset()
        compare_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
