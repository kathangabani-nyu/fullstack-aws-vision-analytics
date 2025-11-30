#!/usr/bin/env python3
"""
Deploy index-photos Lambda with proper code.
"""

import boto3
import zipfile
import io

FUNCTION_NAME = 'index-photos'
REGION = 'us-east-1'

# Lambda function code using urllib (built-in)
LAMBDA_CODE = '''
import json
import boto3
import os
import urllib.request
import urllib.parse
import base64
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'photos')
OPENSEARCH_USERNAME = os.environ.get('OPENSEARCH_USERNAME', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD')

def index_to_opensearch(document):
    """Index document to OpenSearch."""
    try:
        url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_doc"
        
        credentials = f"{OPENSEARCH_USERNAME}:{OPENSEARCH_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = json.dumps(document).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            logger.info(f"Indexed document: {result}")
            return True
            
    except Exception as e:
        logger.error(f"Error indexing to OpenSearch: {str(e)}")
        raise e

def lambda_handler(event, context):
    """Process S3 events and index photos."""
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing: {object_key} from {bucket}")
            
            # Detect labels using Rekognition
            rekognition_response = rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': object_key
                    }
                },
                MaxLabels=10,
                MinConfidence=50
            )
            
            rekognition_labels = [label['Name'].lower() for label in rekognition_response['Labels']]
            logger.info(f"Detected labels: {rekognition_labels}")
            
            # Get custom labels from metadata
            custom_labels = []
            try:
                metadata_response = s3_client.head_object(Bucket=bucket, Key=object_key)
                custom_labels_str = metadata_response.get('Metadata', {}).get('customlabels', '')
                if custom_labels_str:
                    custom_labels = [label.strip().lower() for label in custom_labels_str.split(',') if label.strip()]
                    logger.info(f"Custom labels: {custom_labels}")
            except Exception as e:
                logger.warning(f"Error getting metadata: {str(e)}")
            
            # Combine labels
            all_labels = list(set(rekognition_labels + custom_labels))
            logger.info(f"All labels: {all_labels}")
            
            # Create document
            document = {
                "objectKey": object_key,
                "bucket": bucket,
                "createdTimestamp": datetime.utcnow().isoformat(),
                "labels": all_labels
            }
            
            # Index to OpenSearch
            index_to_opensearch(document)
            logger.info(f"Successfully indexed: {object_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise e
'''

def deploy_lambda():
    """Deploy Lambda function."""
    
    print(f"Deploying Lambda function: {FUNCTION_NAME}")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('lambda_function.py', LAMBDA_CODE)
    
    zip_buffer.seek(0)
    
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    response = lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=zip_buffer.read()
    )
    
    print(f"Updated: {response['FunctionArn']}")
    
    # Update handler
    lambda_client.update_function_configuration(
        FunctionName=FUNCTION_NAME,
        Handler='lambda_function.lambda_handler'
    )
    print("Handler updated")
    
    print("Waiting for update to complete...")
    waiter = lambda_client.get_waiter('function_updated')
    waiter.wait(FunctionName=FUNCTION_NAME)
    print("Deploy complete!")

if __name__ == "__main__":
    deploy_lambda()

