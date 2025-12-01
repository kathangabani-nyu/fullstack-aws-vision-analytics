#!/usr/bin/env python3
"""
Set Gateway Responses for CORS.
"""

import boto3

API_ID = 'awj7t30s2g'
REGION = 'us-east-1'

def set_gateway_responses():
    client = boto3.client('apigateway', region_name=REGION)
    
    response_types = ['DEFAULT_4XX', 'DEFAULT_5XX']
    
    for response_type in response_types:
        print(f"Setting {response_type} response...")
        try:
            client.put_gateway_response(
                restApiId=API_ID,
                responseType=response_type,
                responseParameters={
                    'gatewayresponse.header.Access-Control-Allow-Origin': "'*'",
                    'gatewayresponse.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels'",
                    'gatewayresponse.header.Access-Control-Allow-Methods': "'GET,PUT,POST,DELETE,OPTIONS'"
                }
            )
            print(f"  Done")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Redeploy
    print("\nRedeploying API...")
    client.create_deployment(restApiId=API_ID, stageName='prod', description='Add gateway responses')
    print("Done!")

if __name__ == "__main__":
    set_gateway_responses()

