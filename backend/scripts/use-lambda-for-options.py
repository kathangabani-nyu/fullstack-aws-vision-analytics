#!/usr/bin/env python3
"""
Configure OPTIONS to use Lambda instead of MOCK.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'
LAMBDA_NAME = 'search-photos'
ACCOUNT_ID = '837134650320'

def configure_options_lambda():
    client = boto3.client('apigateway', region_name=REGION)
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Get search resource
    resources = client.get_resources(restApiId=API_ID)['items']
    
    for resource in resources:
        path = resource.get('path', '')
        resource_id = resource['id']
        
        if path == '/search':
            print(f"Configuring OPTIONS for {path}")
            
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
            
            # Create Lambda proxy integration
            lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{LAMBDA_NAME}"
            uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            
            client.put_integration(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=uri
            )
            print("  Created Lambda proxy integration")
            
            # Add Lambda permission for OPTIONS
            try:
                lambda_client.add_permission(
                    FunctionName=LAMBDA_NAME,
                    StatementId=f'apigateway-options-{resource_id}',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{API_ID}/*/OPTIONS/search"
                )
                print("  Added Lambda permission")
            except Exception as e:
                if 'ResourceConflictException' in str(e):
                    print("  Lambda permission already exists")
                else:
                    print(f"  Error adding Lambda permission: {e}")
            
            # Create method response
            client.put_method_response(
                restApiId=API_ID,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200'
            )
            print("  Created method response")
    
    # Deploy
    print("\nDeploying...")
    client.create_deployment(restApiId=API_ID, stageName='prod', description='Use Lambda for OPTIONS')
    print("Done!")

if __name__ == "__main__":
    configure_options_lambda()

