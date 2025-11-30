#!/usr/bin/env python3
"""
Set up CORS for API Gateway endpoints.
"""

import boto3
import json

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def setup_cors():
    """Add CORS support to API Gateway."""
    
    client = boto3.client('apigateway', region_name=REGION)
    
    # Get resources
    resources = client.get_resources(restApiId=API_ID)
    
    for resource in resources['items']:
        resource_id = resource['id']
        path = resource['path']
        
        # Skip root
        if path == '/':
            continue
            
        print(f"Setting up CORS for {path} (ID: {resource_id})")
        
        try:
            # Check if OPTIONS method exists
            try:
                client.get_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS'
                )
                print(f"  OPTIONS method already exists")
            except client.exceptions.NotFoundException:
                # Create OPTIONS method
                client.put_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                print(f"  Created OPTIONS method")
            
            # Set up MOCK integration
            try:
                client.put_integration(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={
                        'application/json': '{"statusCode": 200}'
                    }
                )
                print(f"  Set up MOCK integration")
            except Exception as e:
                print(f"  Integration already exists or error: {e}")
            
            # Set up method response
            try:
                client.put_method_response(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Headers': False,
                        'method.response.header.Access-Control-Allow-Methods': False,
                        'method.response.header.Access-Control-Allow-Origin': False
                    }
                )
                print(f"  Set up method response")
            except Exception as e:
                print(f"  Method response already exists or error: {e}")
            
            # Set up integration response
            try:
                client.put_integration_response(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,PUT,POST,DELETE,OPTIONS'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
                print(f"  Set up integration response")
            except Exception as e:
                print(f"  Integration response error: {e}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Deploy API
    print("\nDeploying API...")
    client.create_deployment(
        restApiId=API_ID,
        stageName='prod',
        description='CORS update'
    )
    print("API deployed!")

if __name__ == "__main__":
    setup_cors()
    print("\nCORS setup complete!")

