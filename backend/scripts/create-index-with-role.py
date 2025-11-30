#!/usr/bin/env python3
"""
Script to create OpenSearch index using a specific IAM role.
This assumes the role first, then creates the index.
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import sys
import json

# Configuration
OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
REGION = 'us-east-1'
INDEX_NAME = 'photos'

# IAM Role ARN that was set as OpenSearch master user
# Update this with the role ARN you used when creating the OpenSearch domain
MASTER_ROLE_ARN = input("Enter the IAM Role ARN you used as OpenSearch master user (or press Enter to use current credentials): ").strip()

def get_credentials_with_role(role_arn):
    """Assume the IAM role and get credentials."""
    sts = boto3.client('sts')
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName='opensearch-index-setup'
        )
        return response['Credentials']
    except Exception as e:
        print(f"Error assuming role: {e}")
        return None

def create_index():
    """Create OpenSearch index with mapping."""
    
    # Get credentials
    if MASTER_ROLE_ARN:
        print(f"Assuming role: {MASTER_ROLE_ARN}")
        creds = get_credentials_with_role(MASTER_ROLE_ARN)
        if not creds:
            print("Failed to assume role. Trying with current credentials...")
            creds = boto3.Session().get_credentials()
        else:
            # Create temporary credentials from assumed role
            awsauth = AWS4Auth(
                creds['AccessKeyId'],
                creds['SecretAccessKey'],
                REGION,
                'es',
                session_token=creds['SessionToken']
            )
    else:
        print("Using current AWS credentials...")
        creds = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            creds.access_key,
            creds.secret_key,
            REGION,
            'es',
            session_token=creds.token
        )
    
    # Index mapping
    mapping = {
        "mappings": {
            "properties": {
                "objectKey": {"type": "keyword"},
                "bucket": {"type": "keyword"},
                "createdTimestamp": {"type": "date"},
                "labels": {"type": "keyword"}
            }
        }
    }
    
    # Create index
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    
    print(f"\nCreating index '{INDEX_NAME}' at: {url}")
    
    try:
        response = requests.put(
            url,
            auth=awsauth,
            json=mapping,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"✓ Index '{INDEX_NAME}' created successfully!")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            if 'resource_already_exists_exception' in str(error_data):
                print(f"⚠ Index '{INDEX_NAME}' already exists.")
                return True
            else:
                print(f"✗ Error: {json.dumps(error_data, indent=2)}")
                return False
        elif response.status_code == 403:
            print(f"✗ Permission denied (403)")
            print(f"Response: {response.text}")
            print("\nPossible solutions:")
            print("1. Make sure the IAM role has OpenSearch permissions")
            print("2. Update OpenSearch domain access policy to allow this role")
            print("3. Use the exact role ARN that was set as master user")
            return False
        else:
            print(f"✗ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenSearch Index Setup (with IAM Role)")
    print("=" * 60)
    print(f"Endpoint: {OPENSEARCH_ENDPOINT}")
    print(f"Region: {REGION}")
    print(f"Index: {INDEX_NAME}")
    print("=" * 60)
    
    if create_index():
        print("\n" + "=" * 60)
        print("Setup complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Setup failed. See error messages above.")
        print("=" * 60)
        sys.exit(1)

