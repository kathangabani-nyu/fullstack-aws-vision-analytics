#!/usr/bin/env python3
"""
Deploy search-photos Lambda with dependencies.
"""

import boto3
import zipfile
import io
import subprocess
import os
import tempfile
import shutil

FUNCTION_NAME = 'search-photos'
REGION = 'us-east-1'

# Lambda function code
LAMBDA_CODE = '''
import json
import boto3
import os
import urllib.request
import urllib.parse
import base64
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'photos')
OPENSEARCH_USERNAME = os.environ.get('OPENSEARCH_USERNAME', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD')
LEX_BOT_ID = os.environ.get('LEX_BOT_ID')
LEX_BOT_ALIAS_ID = os.environ.get('LEX_BOT_ALIAS_ID')

def extract_keywords(query):
    """Extract keywords from query."""
    try:
        if LEX_BOT_ID and LEX_BOT_ALIAS_ID:
            lex_client = boto3.client('lexv2-runtime')
            response = lex_client.recognize_text(
                botId=LEX_BOT_ID,
                botAliasId=LEX_BOT_ALIAS_ID,
                localeId='en_US',
                sessionId='search-session',
                text=query
            )
            logger.info(f"Lex response: {json.dumps(response, default=str)}")
            
            keywords = []
            if response.get('interpretations'):
                interpretation = response['interpretations'][0]
                if 'intent' in interpretation and 'slots' in interpretation['intent']:
                    slots = interpretation['intent']['slots']
                    if slots:
                        for slot_name, slot_value in slots.items():
                            if slot_value and 'value' in slot_value:
                                keyword = slot_value['value'].get('originalValue', '')
                                if keyword:
                                    keywords.append(keyword.lower())
            
            if keywords:
                return keywords
        
        # Fallback: simple keyword extraction
        stop_words = {'show', 'me', 'find', 'photos', 'with', 'of', 'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for'}
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        logger.info(f"Extracted keywords: {keywords}")
        return keywords if keywords else [query.lower().strip()]
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return [query.lower().strip()]

def search_opensearch(keywords):
    """Search OpenSearch for photos matching keywords."""
    try:
        if not keywords or not OPENSEARCH_ENDPOINT:
            return []
        
        should_clauses = []
        for keyword in keywords:
            should_clauses.append({"match": {"labels": keyword}})
        
        query = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            },
            "size": 50
        }
        
        url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_search"
        
        # Create Basic Auth header
        credentials = f"{OPENSEARCH_USERNAME}:{OPENSEARCH_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = json.dumps(query).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
        
        logger.info(f"OpenSearch response received")
        
        photos = []
        if 'hits' in result and 'hits' in result['hits']:
            for hit in result['hits']['hits']:
                if '_source' in hit:
                    photos.append(hit['_source'])
        
        logger.info(f"Found {len(photos)} photos")
        return photos
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

def lambda_handler(event, context):
    """Handle search requests."""
    logger.info(f"Event: {json.dumps(event)}")
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        query_params = event.get('queryStringParameters') or {}
        query = query_params.get('q', '')
        
        if not query:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([])
            }
        
        logger.info(f"Search query: {query}")
        
        keywords = extract_keywords(query)
        
        if not keywords:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([])
            }
        
        results = search_opensearch(keywords)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
'''

def deploy_lambda():
    """Deploy Lambda function."""
    
    print(f"Deploying Lambda function: {FUNCTION_NAME}")
    
    # Create zip file with just the code (using urllib instead of requests)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('lambda_function.py', LAMBDA_CODE)
    
    zip_buffer.seek(0)
    
    # Update Lambda function
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    response = lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=zip_buffer.read()
    )
    
    print(f"Updated: {response['FunctionArn']}")
    
    # Wait for update to complete
    print("Waiting for update to complete...")
    waiter = lambda_client.get_waiter('function_updated')
    waiter.wait(FunctionName=FUNCTION_NAME)
    print("Deploy complete!")

if __name__ == "__main__":
    deploy_lambda()

