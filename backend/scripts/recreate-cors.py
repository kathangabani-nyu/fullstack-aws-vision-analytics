#!/usr/bin/env python3
"""
Recreate CORS configuration from scratch.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def recreate_cors():
    client = boto3.client('apigateway', region_name=REGION)
    
    # Get resources
    resources = client.get_resources(restApiId=API_ID)['items']
    
    for resource in resources:
        path = resource.get('path', '')
        resource_id = resource['id']
        
        if path in ['/search', '/photos/{key}', '/photos']:
            print(f"\nRecreating CORS for {path} ({resource_id})")
            
            # Delete existing OPTIONS if it exists
            try:
                client.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
                print(f"  Deleted existing OPTIONS")
            except Exception as e:
                print(f"  No existing OPTIONS to delete")
            
            # Create new OPTIONS method
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            print(f"  Created OPTIONS method")
            
            # Create MOCK integration
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            print(f"  Created MOCK integration")
            
            # Add method response with CORS headers
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                },
                responseModels={'application/json': 'Empty'}
            )
            print(f"  Created method response")
            
            # Add integration response with CORS headers
            client.put_integration_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,PUT,POST,DELETE,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                },
                responseTemplates={'application/json': ''}
            )
            print(f"  Created integration response")
    
    # Redeploy
    print("\nRedeploying API...")
    client.create_deployment(restApiId=API_ID, stageName='prod', description='Recreate CORS')
    print("Done!")

if __name__ == "__main__":
    recreate_cors()

