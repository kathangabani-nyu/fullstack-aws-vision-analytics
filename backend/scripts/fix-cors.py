#!/usr/bin/env python3
"""
Fix CORS for API Gateway after redeployment.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def fix_cors():
    client = boto3.client('apigateway', region_name=REGION)
    
    # Get resources
    resources = client.get_resources(restApiId=API_ID)['items']
    
    for resource in resources:
        path = resource.get('path', '')
        resource_id = resource['id']
        
        # Add OPTIONS method for CORS
        if path in ['/search', '/photos/{key}', '/photos']:
            print(f"Adding CORS for {path}")
            
            # Check if OPTIONS exists
            try:
                client.get_method(restApiId=API_ID, resourceId=resource_id, httpMethod='OPTIONS')
                print(f"  OPTIONS already exists for {path}")
            except:
                # Create OPTIONS method
                client.put_method(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    authorizationType='NONE'
                )
                
                # Create MOCK integration
                client.put_integration(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    type='MOCK',
                    requestTemplates={'application/json': '{"statusCode": 200}'}
                )
                
                # Add method response
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
                
                # Add integration response
                client.put_integration_response(
                    restApiId=API_ID,
                    resourceId=resource_id,
                    httpMethod='OPTIONS',
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET,PUT,POST,OPTIONS'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    responseTemplates={'application/json': ''}
                )
                print(f"  Added OPTIONS for {path}")
    
    # Redeploy
    print("\nRedeploying API...")
    client.create_deployment(restApiId=API_ID, stageName='prod', description='Fix CORS')
    print("Done!")

if __name__ == "__main__":
    fix_cors()

