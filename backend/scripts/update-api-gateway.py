#!/usr/bin/env python3
"""
Update API Gateway to properly handle file uploads with Content-Type.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'
RESOURCE_ID = 'lwfhop'  # /photos/{key}

def update_api():
    """Update API Gateway PUT method to pass Content-Type."""
    
    client = boto3.client('apigateway', region_name=REGION)
    
    print("Updating PUT method integration...")
    
    # Get current integration
    try:
        integration = client.get_integration(
            restApiId=API_ID,
            resourceId=RESOURCE_ID,
            httpMethod='PUT'
        )
        print(f"Current integration: {integration.get('type')}")
        print(f"Current request parameters: {integration.get('requestParameters', {})}")
    except Exception as e:
        print(f"Error getting integration: {e}")
        return
    
    # Update method to accept Content-Type header
    try:
        client.update_method(
            restApiId=API_ID,
            resourceId=RESOURCE_ID,
            httpMethod='PUT',
            patchOperations=[
                {
                    'op': 'add',
                    'path': '/requestParameters/method.request.header.Content-Type',
                    'value': 'false'
                }
            ]
        )
        print("Added Content-Type to method request parameters")
    except Exception as e:
        print(f"Content-Type parameter may already exist: {e}")
    
    # Update integration to pass Content-Type to S3
    try:
        client.update_integration(
            restApiId=API_ID,
            resourceId=RESOURCE_ID,
            httpMethod='PUT',
            patchOperations=[
                {
                    'op': 'add',
                    'path': '/requestParameters/integration.request.header.Content-Type',
                    'value': 'method.request.header.Content-Type'
                }
            ]
        )
        print("Added Content-Type to integration request parameters")
    except Exception as e:
        print(f"Error updating integration: {e}")
    
    # Deploy API
    print("\nDeploying API...")
    client.create_deployment(
        restApiId=API_ID,
        stageName='prod',
        description='Content-Type passthrough update'
    )
    print("API deployed!")

if __name__ == "__main__":
    update_api()
    print("\nAPI Gateway update complete!")

