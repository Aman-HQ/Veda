"""
Quick test script for B09 Admin & Observability features.
Run this after starting the backend server to verify all endpoints are working.

Usage:
    python scripts/test_b09.py
"""

import asyncio
import httpx
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
# Replace with your admin user token
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ZTJhOWQ3Yy0zNjU4LTRhYzItOTM0My1lZmIxOWIwMTczZGMiLCJlbWFpbCI6ImFtYW5AZ21haWwuY29tIiwiZXhwIjoxNzYxNDE1ODAyLCJ0eXBlIjoiYWNjZXNzIn0.3UaZV-PAJWCcYNUiPP2ST-GzD2VCbS8rakPKdjQXuj8"  # Get from /api/auth/login with admin user


async def test_health():
    """Test basic health endpoint."""
    print("\n" + "="*60)
    print("Testing /health endpoint...")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_admin_stats():
    """Test admin statistics endpoint."""
    print("\n" + "="*60)
    print("Testing /api/admin/stats endpoint...")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/admin/stats?days=7",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nOverview:")
            print(f"  Total Users: {data['overview']['total_users']}")
            print(f"  Total Conversations: {data['overview']['total_conversations']}")
            print(f"  Total Messages: {data['overview']['total_messages']}")
            print(f"  Recent Messages: {data['overview']['recent_messages']}")
            
            print("\nModeration:")
            print(f"  Total Checked: {data['moderation'].get('total_checked', 0)}")
            print(f"  Total Blocked: {data['moderation'].get('total_blocked', 0)}")
            print(f"  Total Flagged: {data['moderation'].get('total_flagged', 0)}")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False


async def test_admin_metrics():
    """Test admin real-time metrics endpoint."""
    print("\n" + "="*60)
    print("Testing /api/admin/metrics endpoint...")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/admin/metrics",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nUptime:")
            print(f"  {data['uptime']['formatted']}")
            print(f"  Started at: {data['uptime']['started_at']}")
            
            print("\nConversations:")
            print(f"  Active (last 24h): {data['conversations']['active_last_24h']}")
            
            print("\nMessages:")
            print(f"  Today: {data['messages']['today']}")
            print(f"  Flagged (total): {data['messages']['flagged_total']}")
            print(f"  Flagged (last 24h): {data['messages']['flagged_last_24h']}")
            
            print("\nSystem Resources:")
            print(f"  Process Memory: {data['system_resources']['process']['memory_mb']} MB")
            print(f"  Process CPU: {data['system_resources']['process']['cpu_percent']}%")
            print(f"  System Memory: {data['system_resources']['system']['memory_percent']}%")
            print(f"  System CPU: {data['system_resources']['system']['cpu_percent']}%")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False


async def test_system_health():
    """Test system health check endpoint."""
    print("\n" + "="*60)
    print("Testing /api/admin/system/health endpoint...")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/admin/system/health",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nOverall Status: {data['overall_status']}")
            
            print("\nComponents:")
            for component, status in data['components'].items():
                print(f"  {component}: {status.get('status', 'unknown')}")
            
            return data['overall_status'] == 'healthy'
        else:
            print(f"Error: {response.json()}")
            return False


async def test_moderation_stats():
    """Test moderation statistics endpoint."""
    print("\n" + "="*60)
    print("Testing /api/admin/moderation/stats endpoint...")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/admin/moderation/stats",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nHealth: {data['health']['status']}")
            print(f"Rules Loaded: {data['health'].get('rules_loaded', False)}")
            
            print("\nRules Breakdown:")
            for severity, count in data['rules_breakdown'].items():
                print(f"  {severity}: {count} keywords")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False


async def test_metrics_endpoint():
    """Test Prometheus metrics endpoint (if enabled)."""
    print("\n" + "="*60)
    print("Testing /metrics endpoint...")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/metrics")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Just show first 500 characters
            content = response.text[:500]
            print(f"\nMetrics Sample:\n{content}...")
            print("\n✓ Prometheus metrics endpoint is enabled")
            return True
        elif response.status_code == 404:
            print("\n⚠ Metrics endpoint not found (ENABLE_METRICS may be false)")
            return True
        else:
            print(f"Error: {response.text}")
            return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("B09 Admin & Observability Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if ADMIN_TOKEN == "your-admin-token-here":
        print("\n⚠ WARNING: Please set ADMIN_TOKEN in the script!")
        print("Get a token by:")
        print("  1. Register/login with an admin user")
        print("  2. Copy the access_token from the response")
        print("  3. Update ADMIN_TOKEN in this script")
        return
    
    # Run tests
    results = {
        "Health Check": await test_health(),
        "Admin Stats": await test_admin_stats(),
        "Admin Metrics": await test_admin_metrics(),
        "System Health": await test_system_health(),
        "Moderation Stats": await test_moderation_stats(),
        "Prometheus Metrics": await test_metrics_endpoint()
    }
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! B09 implementation is working correctly.")
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
