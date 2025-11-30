#!/usr/bin/env python3
"""
Script to create OpenSearch index with proper mapping.
Run this after creating your OpenSearch domain.
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import sys
import json

# Configuration - UPDATE THIS with your OpenSearch endpoint
OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
REGION = 'us-east-1'
INDEX_NAME = 'photos'

def create_index():
    """Create OpenSearch index with mapping."""
    
    # Get AWS credentials from current session
    try:
        credentials = boto3.Session().get_credentials()
        if not credentials:
            print("Error: No AWS credentials found. Configure AWS CLI first.")
            sys.exit(1)
    except Exception as e:
        print(f"Error getting credentials: {e}")
        sys.exit(1)
    
    # Create AWS Signature Version 4 auth
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        'es',
        session_token=credentials.token
    )
    
    # Index mapping
    mapping = {
        "mappings": {
            "properties": {
                "objectKey": {
                    "type": "keyword"
                },
                "bucket": {
                    "type": "keyword"
                },
                "createdTimestamp": {
                    "type": "date"
                },
                "labels": {
                    "type": "keyword"
                }
            }
        }
    }
    
    # Create index
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    
    print(f"Creating index '{INDEX_NAME}' at: {url}")
    print(f"Mapping: {json.dumps(mapping, indent=2)}")
    
    try:
        response = requests.put(
            url,
            auth=awsauth,
            json=mapping,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"✓ Index '{INDEX_NAME}' created successfully!")
            print(f"Response: {response.json()}")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            if 'resource_already_exists_exception' in str(error_data):
                print(f"⚠ Index '{INDEX_NAME}' already exists.")
                return True
            else:
                print(f"✗ Error: {error_data}")
                return False
        else:
            print(f"✗ Error creating index:")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False

def verify_index():
    """Verify the index was created."""
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        'es',
        session_token=credentials.token
    )
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    
    try:
        response = requests.get(url, auth=awsauth, timeout=30)
        
        if response.status_code == 200:
            print(f"\n✓ Index verification successful!")
            index_info = response.json()
            print(f"  Index: {INDEX_NAME}")
            print(f"  Settings: {json.dumps(index_info.get('settings', {}), indent=2)}")
            return True
        else:
            print(f"✗ Index verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenSearch Index Setup")
    print("=" * 60)
    print(f"Endpoint: {OPENSEARCH_ENDPOINT}")
    print(f"Region: {REGION}")
    print(f"Index: {INDEX_NAME}")
    print("=" * 60)
    
    if create_index():
        verify_index()
        print("\n" + "=" * 60)
        print("Setup complete! You can now update Lambda environment variables.")
        print(f"OPENSEARCH_ENDPOINT={OPENSEARCH_ENDPOINT}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Setup failed. Please check the error messages above.")
        print("=" * 60)
        sys.exit(1)

