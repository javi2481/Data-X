#!/usr/bin/env python3
"""
Backend API Testing for Code Audit Report Viewer
Tests the FastAPI endpoints that serve audit report data
"""

import requests
import sys
import json
from datetime import datetime

class AuditReportAPITester:
    def __init__(self, base_url="https://datax-code-review.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status=200, expected_keys=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Validate response structure if expected_keys provided
                if expected_keys and response.status_code == 200:
                    try:
                        data = response.json()
                        for key in expected_keys:
                            if key not in data:
                                print(f"⚠️  Warning: Expected key '{key}' not found in response")
                            else:
                                print(f"   ✓ Found key: {key}")
                    except json.JSONDecodeError:
                        print(f"⚠️  Warning: Response is not valid JSON")
                
                return True, response
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}...")
                return False, response

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            return False, None
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, None
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_full_report(self):
        """Test /api/report endpoint"""
        success, response = self.run_test(
            "Full Audit Report",
            "GET",
            "api/report",
            expected_keys=["meta", "sections"]
        )
        
        if success and response:
            try:
                data = response.json()
                meta = data.get("meta", {})
                stats = meta.get("stats", {})
                
                # Validate expected stats
                expected_stats = {
                    "total_issues": 23,
                    "critical": 4,
                    "high": 7,
                    "medium": 8,
                    "low": 4
                }
                
                print("   📊 Validating stats:")
                for key, expected_value in expected_stats.items():
                    actual_value = stats.get(key)
                    if actual_value == expected_value:
                        print(f"   ✓ {key}: {actual_value}")
                    else:
                        print(f"   ❌ {key}: expected {expected_value}, got {actual_value}")
                
                # Validate sections
                sections = data.get("sections", [])
                expected_sections = ["architecture", "bugs", "refactoring", "ai_ml", "action_plan"]
                print("   📋 Validating sections:")
                for section_key in expected_sections:
                    found = any(s.get("key") == section_key for s in sections)
                    if found:
                        print(f"   ✓ Section: {section_key}")
                    else:
                        print(f"   ❌ Missing section: {section_key}")
                        
            except Exception as e:
                print(f"   ⚠️  Error validating response: {e}")
        
        return success

    def test_issues_endpoint(self):
        """Test /api/report/issues endpoint"""
        success, response = self.run_test(
            "Issues Endpoint",
            "GET",
            "api/report/issues"
        )
        
        if success and response:
            try:
                issues = response.json()
                print(f"   📝 Found {len(issues)} total issues")
                
                # Test filtering by severity
                for severity in ["critical", "high", "medium", "low"]:
                    filter_success, filter_response = self.run_test(
                        f"Issues Filter - {severity}",
                        "GET",
                        f"api/report/issues?severity={severity}"
                    )
                    if filter_success and filter_response:
                        filtered_issues = filter_response.json()
                        print(f"   ✓ {severity}: {len(filtered_issues)} issues")
                
                # Test search functionality
                search_success, search_response = self.run_test(
                    "Issues Search - FAISS",
                    "GET",
                    "api/report/issues?q=FAISS"
                )
                if search_success and search_response:
                    search_results = search_response.json()
                    print(f"   🔍 FAISS search: {len(search_results)} results")
                    
            except Exception as e:
                print(f"   ⚠️  Error validating issues: {e}")
        
        return success

    def test_export_endpoint(self):
        """Test /api/report/export.md endpoint"""
        success, response = self.run_test(
            "Export Markdown",
            "GET",
            "api/report/export.md"
        )
        
        if success and response:
            content = response.text
            print(f"   📄 Markdown content length: {len(content)} characters")
            if "# Auditoría de Código" in content:
                print("   ✓ Contains expected markdown header")
            else:
                print("   ⚠️  Missing expected markdown header")
        
        return success

    def test_summary_endpoint(self):
        """Test /api/report/summary endpoint"""
        success, response = self.run_test(
            "Report Summary",
            "GET",
            "api/report/summary",
            expected_keys=["meta", "sections"]
        )
        return success

def main():
    print("🚀 Starting Code Audit Report API Tests")
    print("=" * 50)
    
    tester = AuditReportAPITester()
    
    # Run all tests
    tests = [
        tester.test_full_report,
        tester.test_summary_endpoint,
        tester.test_issues_endpoint,
        tester.test_export_endpoint,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API tests passed!")
        return 0
    else:
        print("⚠️  Some API tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())