#!/usr/bin/env python3
"""
Test script for the AquaScene Agentic Workflow System
This script tests the complete workflow from connection to metadata table creation
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
DEMO_API_KEY = "demo_key_placeholder"  # Replace with actual API key
DEMO_BASE_ID = "demo_base_placeholder"  # Replace with actual base ID

class WorkflowTester:
    """Test the agentic workflow system"""
    
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.session = requests.Session()
    
    def test_connection(self, api_key: str, base_id: str) -> Dict[str, Any]:
        """Test Airtable connection"""
        print("🔍 Testing Airtable connection...")
        
        response = self.session.post(
            f"{self.api_base}/api/v1/workflows/airtable/test-connection",
            json={
                "airtable_api_key": api_key,
                "airtable_base_id": base_id,
                "workflow_type": "connection_test"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Connection successful: {result.get('message', '')}")
                tables = result.get('tables', [])
                print(f"📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table}")
                return result
            else:
                print(f"❌ Connection failed: {result.get('message', '')}")
                return result
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return {"success": False, "message": response.text}
    
    def start_analysis(self, api_key: str, base_id: str) -> Dict[str, Any]:
        """Start schema analysis"""
        print("🚀 Starting schema analysis...")
        
        response = self.session.post(
            f"{self.api_base}/api/v1/workflows/airtable/schema-analysis",
            json={
                "airtable_api_key": api_key,
                "airtable_base_id": base_id,
                "workflow_type": "schema_analysis"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result.get('workflow_id')
            print(f"✅ Analysis started with workflow ID: {workflow_id}")
            return result
        else:
            print(f"❌ Failed to start analysis: {response.text}")
            return {"error": response.text}
    
    def monitor_workflow(self, workflow_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Monitor workflow progress"""
        print(f"⏳ Monitoring workflow {workflow_id}...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    f"{self.api_base}/api/v1/workflows/status/{workflow_id}"
                )
                
                if response.status_code == 200:
                    status = response.json()
                    
                    print(f"📊 Status: {status.get('status', 'unknown')} - Progress: {status.get('progress', 0):.1f}%")
                    
                    # Print latest logs
                    logs = status.get('logs', [])
                    if logs:
                        latest_log = logs[-1] if logs else "No logs"
                        print(f"💬 Latest: {latest_log}")
                    
                    if status.get('status') == 'completed':
                        print("🎉 Workflow completed successfully!")
                        return status
                    elif status.get('status') == 'failed':
                        print(f"❌ Workflow failed: {status.get('error', 'Unknown error')}")
                        return status
                
                time.sleep(5)  # Wait 5 seconds before next check
            
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(5)
        
        print("⏰ Workflow monitoring timed out")
        return {"status": "timeout"}
    
    def create_metadata_table(self, analysis_workflow_id: str) -> Dict[str, Any]:
        """Create metadata table from analysis results"""
        print("📋 Creating metadata table...")
        
        response = self.session.post(
            f"{self.api_base}/api/v1/workflows/airtable/create-metadata-table",
            params={"workflow_id": analysis_workflow_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            metadata_workflow_id = result.get('workflow_id')
            print(f"✅ Metadata table creation started with workflow ID: {metadata_workflow_id}")
            return result
        else:
            print(f"❌ Failed to create metadata table: {response.text}")
            return {"error": response.text}
    
    def download_results(self, workflow_id: str, file_type: str) -> bool:
        """Download workflow results"""
        print(f"📥 Downloading {file_type} results...")
        
        response = self.session.get(
            f"{self.api_base}/api/v1/workflows/download/{workflow_id}/{file_type}"
        )
        
        if response.status_code == 200:
            filename = f"workflow_{workflow_id}_{file_type}.{'json' if 'json' in file_type else 'txt'}"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
            return True
        else:
            print(f"❌ Failed to download {file_type}: {response.text}")
            return False
    
    def run_full_test(self, api_key: str, base_id: str) -> bool:
        """Run the complete workflow test"""
        print("🎯 Starting comprehensive workflow test...")
        print("=" * 60)
        
        # Step 1: Test connection
        connection_result = self.test_connection(api_key, base_id)
        if not connection_result.get('success'):
            print("❌ Connection test failed - aborting workflow test")
            return False
        
        print("\n" + "=" * 60)
        
        # Step 2: Start analysis
        analysis_result = self.start_analysis(api_key, base_id)
        if 'error' in analysis_result:
            print("❌ Analysis start failed - aborting workflow test")
            return False
        
        analysis_workflow_id = analysis_result.get('workflow_id')
        
        # Step 3: Monitor analysis
        analysis_status = self.monitor_workflow(analysis_workflow_id)
        if analysis_status.get('status') != 'completed':
            print("❌ Analysis failed or timed out - aborting workflow test")
            return False
        
        print("\n" + "=" * 60)
        
        # Step 4: Download analysis results
        self.download_results(analysis_workflow_id, 'json')
        self.download_results(analysis_workflow_id, 'summary')
        
        print("\n" + "=" * 60)
        
        # Step 5: Create metadata table
        metadata_result = self.create_metadata_table(analysis_workflow_id)
        if 'error' in metadata_result:
            print("❌ Metadata table creation failed")
            return False
        
        metadata_workflow_id = metadata_result.get('workflow_id')
        
        # Step 6: Monitor metadata table creation
        metadata_status = self.monitor_workflow(metadata_workflow_id)
        if metadata_status.get('status') != 'completed':
            print("❌ Metadata table creation failed or timed out")
            return False
        
        # Step 7: Download metadata table files
        self.download_results(metadata_workflow_id, 'instructions')
        self.download_results(metadata_workflow_id, 'structure')
        self.download_results(metadata_workflow_id, 'records')
        
        print("\n" + "=" * 60)
        print("🎉 COMPLETE WORKFLOW TEST SUCCESSFUL!")
        print("=" * 60)
        print(f"✅ Connection tested successfully")
        print(f"✅ Schema analysis completed: {analysis_workflow_id}")
        print(f"✅ Metadata table creation completed: {metadata_workflow_id}")
        print(f"✅ All result files downloaded")
        
        return True
    
    def test_api_endpoints(self) -> bool:
        """Test basic API endpoints"""
        print("🔧 Testing API endpoints...")
        
        # Test workflow list endpoint
        try:
            response = self.session.get(f"{self.api_base}/api/v1/workflows/")
            if response.status_code == 200:
                workflows = response.json()
                print(f"✅ Workflow list endpoint: {len(workflows)} workflows")
            else:
                print(f"❌ Workflow list endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Workflow list endpoint error: {e}")
            return False
        
        # Test health endpoint
        try:
            response = self.session.get(f"{self.api_base}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Health endpoint: {health.get('status', 'unknown')}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
        
        return True


def main():
    """Main test execution"""
    print("AquaScene Agentic Workflow System - End-to-End Test")
    print("=" * 55)
    
    # Check if we have API credentials
    api_key = os.getenv('AIRTABLE_API_KEY', DEMO_API_KEY)
    base_id = os.getenv('AIRTABLE_BASE_ID', DEMO_BASE_ID)
    
    if api_key == "demo_key_placeholder":
        print("⚠️  WARNING: Using placeholder API key")
        print("   Set AIRTABLE_API_KEY environment variable for real testing")
    
    if base_id == "demo_base_placeholder":
        print("⚠️  WARNING: Using placeholder Base ID")
        print("   Set AIRTABLE_BASE_ID environment variable for real testing")
    
    # Initialize tester
    tester = WorkflowTester(API_BASE_URL)
    
    # Test basic API endpoints first
    print("\n" + "=" * 60)
    if not tester.test_api_endpoints():
        print("❌ Basic API tests failed - check if services are running")
        return 1
    
    # If we have real credentials, run full test
    if api_key != "demo_key_placeholder" and base_id != "demo_base_placeholder":
        print("\n" + "=" * 60)
        if tester.run_full_test(api_key, base_id):
            print("\n🎯 ALL TESTS PASSED!")
            return 0
        else:
            print("\n❌ WORKFLOW TEST FAILED!")
            return 1
    else:
        print("\n🔧 API TESTS PASSED!")
        print("   To run full workflow test, set AIRTABLE_API_KEY and AIRTABLE_BASE_ID")
        return 0


if __name__ == "__main__":
    sys.exit(main())