#!/usr/bin/env python3
"""
Fix OPTIONS with simpler configuration.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def fix_options():
    client = boto3.client('apigateway', region_name=REGION)
    
    # Get search resource
    resources = client.get_resources(restApiId=API_ID)['items']
    
    paths_to_fix = ['/search', '/photos/{key}', '/photos']
    
    for resource in resources:
        path = resource.get('path', '')
        resource_id = resource['id']
        
        if path in paths_to_fix:
            print(f"\nFixing OPTIONS for {path}")
            
            # Delete existing OPTIONS
            try:
                client.delete_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
                print("  Deleted existing OPTIONS")
            except:
                pass
            
            # Create OPTIONS method
            client.put_method(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE',
                apiKeyRequired=False
            )
            print("  Created OPTIONS method")
            
            # Create MOCK integration with correct passthrough
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                passthroughBehavior='WHEN_NO_MATCH',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            print("  Created MOCK integration")
            
            # Create method response
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            print("  Created method response")
            
            # Create integration response
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
                responseTemplates={
                    'application/json': ''
                }
            )
            print("  Created integration response")
    
    # Deploy
    print("\nDeploying...")
    client.create_deployment(restApiId=API_ID, stageName='prod', description='Fixed OPTIONS')
    print("Done!")

if __name__ == "__main__":
    fix_options()

