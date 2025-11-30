import json
import boto3
import os
import requests
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

# OpenSearch configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'photos')

# OpenSearch master user credentials
OPENSEARCH_USERNAME = os.environ.get('OPENSEARCH_USERNAME', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD')


def lambda_handler(event, context):
    """
    Lambda function triggered by S3 PUT events.
    Detects labels in images using Rekognition and indexes them in OpenSearch.
    """
    try:
        # Extract S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f"Processing image: {object_key} from bucket: {bucket}")
            
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
            
            # Extract labels from Rekognition response
            rekognition_labels = [label['Name'].lower() for label in rekognition_response['Labels']]
            logger.info(f"Rekognition detected labels: {rekognition_labels}")
            
            # Get S3 object metadata to retrieve custom labels
            try:
                metadata_response = s3_client.head_object(Bucket=bucket, Key=object_key)
                custom_labels_str = metadata_response.get('Metadata', {}).get('customlabels', '')
                
                # Parse custom labels (comma-separated)
                custom_labels = []
                if custom_labels_str:
                    custom_labels = [label.strip() for label in custom_labels_str.split(',') if label.strip()]
                    logger.info(f"Custom labels found: {custom_labels}")
            except Exception as e:
                logger.warning(f"Error retrieving metadata: {str(e)}")
                custom_labels = []
            
            # Combine all labels
            all_labels = list(set(rekognition_labels + custom_labels))
            logger.info(f"All labels to index: {all_labels}")
            
            # Get creation timestamp
            created_timestamp = datetime.utcnow().isoformat()
            
            # Create document for OpenSearch
            document = {
                "objectKey": object_key,
                "bucket": bucket,
                "createdTimestamp": created_timestamp,
                "labels": all_labels
            }
            
            # Index document in OpenSearch
            opensearch_url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_doc"
            
            response = requests.post(
                opensearch_url,
                auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
                json=document,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully indexed document: {object_key}")
            else:
                logger.error(f"Failed to index document. Status: {response.status_code}, Response: {response.text}")
                raise Exception(f"OpenSearch indexing failed: {response.text}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed image(s)')
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise e

