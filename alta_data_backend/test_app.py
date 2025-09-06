#!/usr/bin/env python3
"""
Quick health check script for Alta Data backend
"""
import requests
import time
import sys

def test_endpoint(url, name, expected_status=200):
    """Test a single endpoint"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status:
            print(f"✅ {name}: OK ({response.status_code})")
            return True
        else:
            print(f"❌ {name}: FAILED ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def main():
    """Run all health checks"""
    print("🔍 Testing Alta Data Backend Services...")
    print("=" * 50)
    
    # Wait a bit for services to start
    print("⏳ Waiting 10 seconds for services to start...")
    time.sleep(10)
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000/health", "API Health Check"),
        ("http://localhost:8000/docs", "API Documentation"),
        ("http://localhost:15672", "RabbitMQ Management"),
        ("http://localhost:5555", "Flower Monitoring"),
    ]
    
    results = []
    for url, name in endpoints:
        results.append(test_endpoint(url, name))
        time.sleep(1)  # Small delay between requests
    
    print("=" * 50)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 All services are running! ({success_count}/{total_count})")
        print("\n📋 Available Services:")
        print("  • API: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • RabbitMQ: http://localhost:15672 (guest/guest)")
        print("  • Flower: http://localhost:5555")
        return True
    else:
        print(f"⚠️  Some services are not responding ({success_count}/{total_count})")
        print("\n🔧 Troubleshooting:")
        print("  • Check container status: docker-compose ps")
        print("  • Check logs: docker-compose logs")
        print("  • Restart services: docker-compose restart")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
