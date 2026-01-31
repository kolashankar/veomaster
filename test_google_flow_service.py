#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from services.google_flow_service import google_flow_service
from services.database_service import db_service

async def test_google_flow():
    print("Testing Google Flow Service...")
    print("=" * 60)
    
    # Test 1: Initialize browser
    print("\n1. Testing browser initialization...")
    try:
        success = await google_flow_service.initialize_browser()
        if success:
            print("   ✅ Browser initialized successfully")
        else:
            print("   ❌ Browser initialization failed")
            return
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Check login
    print("\n2. Testing Google Flow login...")
    try:
        logged_in = await google_flow_service.check_and_login()
        if logged_in:
            print("   ✅ Login successful")
        else:
            print("   ❌ Login failed")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await google_flow_service.close_browser()
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_google_flow())
