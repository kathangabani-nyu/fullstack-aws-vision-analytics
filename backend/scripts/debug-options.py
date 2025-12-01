#!/usr/bin/env python3
"""
Debug OPTIONS method configuration.
"""

import boto3
import json

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def debug_options():
    client = boto3.client('apigateway', region_name=REGION)
    
    # Get resources
    resources = client.get_resources(restApiId=API_ID)['items']
    
    for resource in resources:
        path = resource.get('path', '')
        resource_id = resource['id']
        
        if path == '/search':
            print(f"Resource: {path} ({resource_id})")
            
            # Get OPTIONS method
            try:
                method = client.get_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS'
                )
                print(f"\nFull OPTIONS method configuration:")
                print(json.dumps(method, indent=2, default=str))
            except Exception as e:
                print(f"Error getting OPTIONS method: {e}")
            
            # Test invoke
            print("\n\nTest invoking OPTIONS...")
            try:
                test_result = client.test_invoke_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS'
                )
                print(f"Status: {test_result['status']}")
                print(f"Headers: {test_result.get('headers', {})}")
                print(f"Body: {test_result.get('body', '')}")
                print(f"Log: {test_result.get('log', '')[:500]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    debug_options()

