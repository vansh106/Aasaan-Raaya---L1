#!/usr/bin/env python3
"""
Test script to verify Swagger documentation is accessible and properly configured.
Run this after starting the server to verify everything is working.
"""

import requests
import sys
from typing import Dict, Any


def test_endpoint(url: str, name: str) -> bool:
    """Test if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: {url}")
            return True
        else:
            print(f"❌ {name}: {url} (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: {url} (Error: {str(e)})")
        return False


def check_openapi_schema(base_url: str) -> bool:
    """Check if OpenAPI schema is valid"""
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            
            # Check required OpenAPI fields
            required_fields = ["openapi", "info", "paths"]
            missing_fields = [field for field in required_fields if field not in schema]
            
            if missing_fields:
                print(f"❌ OpenAPI schema missing fields: {missing_fields}")
                return False
            
            # Check info section
            info = schema.get("info", {})
            if "title" in info and "version" in info:
                print(f"✅ OpenAPI Schema: {info['title']} v{info['version']}")
            
            # Count endpoints
            paths = schema.get("paths", {})
            endpoint_count = len(paths)
            print(f"   📋 Endpoints documented: {endpoint_count}")
            
            # Check security schemes
            components = schema.get("components", {})
            security_schemes = components.get("securitySchemes", {})
            if security_schemes:
                print(f"   🔒 Security schemes: {', '.join(security_schemes.keys())}")
            
            # Check tags
            tags = schema.get("tags", [])
            if tags:
                tag_names = [tag.get("name") for tag in tags]
                print(f"   🏷️  Categories: {', '.join(tag_names)}")
            
            return True
        else:
            print(f"❌ OpenAPI schema not accessible (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAPI schema error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ OpenAPI schema parsing error: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("🔍 Testing Swagger Documentation")
    print("=" * 60)
    print()
    
    base_url = "http://localhost:8000"
    
    # Test basic connectivity
    print("1️⃣  Testing Basic Connectivity...")
    print("-" * 60)
    health_ok = test_endpoint(f"{base_url}/health", "Health Check")
    print()
    
    if not health_ok:
        print("⚠️  Server doesn't appear to be running.")
        print("   Please start the server with: uvicorn main:app --reload")
        sys.exit(1)
    
    # Test documentation endpoints
    print("2️⃣  Testing Documentation Endpoints...")
    print("-" * 60)
    results = []
    results.append(test_endpoint(f"{base_url}/docs", "Swagger UI"))
    results.append(test_endpoint(f"{base_url}/redoc", "ReDoc"))
    results.append(test_endpoint(f"{base_url}/openapi.json", "OpenAPI Schema"))
    print()
    
    # Check OpenAPI schema details
    print("3️⃣  Analyzing OpenAPI Schema...")
    print("-" * 60)
    schema_ok = check_openapi_schema(base_url)
    print()
    
    # Summary
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    total_tests = len(results) + 1  # +1 for health check
    passed_tests = sum(results) + (1 if health_ok else 0)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests and schema_ok:
        print()
        print("🎉 All tests passed! Your Swagger documentation is working perfectly.")
        print()
        print("📚 Access your documentation:")
        print(f"   • Swagger UI: {base_url}/docs")
        print(f"   • ReDoc:      {base_url}/redoc")
        print(f"   • OpenAPI:    {base_url}/openapi.json")
        print()
        print("💡 Next Steps:")
        print("   1. Open Swagger UI in your browser")
        print("   2. Click 'Authorize' and enter your API key")
        print("   3. Try out the endpoints!")
        sys.exit(0)
    else:
        print()
        print("⚠️  Some tests failed. Please check the errors above.")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Make sure the server is running: uvicorn main:app --reload")
        print("   2. Check if port 8000 is not in use by another process")
        print("   3. Verify your .env file is properly configured")
        print("   4. Check the server logs for errors")
        sys.exit(1)


if __name__ == "__main__":
    main()

