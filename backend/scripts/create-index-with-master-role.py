#!/usr/bin/env python3
"""
Script to create OpenSearch index using the master user IAM role.
This assumes the IAM role that was set as OpenSearch master user.
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

# The IAM role ARN that was set as OpenSearch master user
# You need to provide this - check OpenSearch Console → Security → Fine-grained access control
MASTER_ROLE_ARN = input("Enter the IAM Role ARN set as OpenSearch master user (or press Enter to try current credentials): ").strip()

def assume_role_and_create_index(role_arn):
    """Assume the IAM role and create index."""
    sts = boto3.client('sts')
    
    try:
        print(f"Assuming role: {role_arn}")
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName='opensearch-index-setup'
        )
        creds = response['Credentials']
        
        # Create auth with assumed role credentials
        awsauth = AWS4Auth(
            creds['AccessKeyId'],
            creds['SecretAccessKey'],
            REGION,
            'es',
            session_token=creds['SessionToken']
        )
        
        return awsauth
        
    except Exception as e:
        print(f"Error assuming role: {e}")
        return None

def create_index(awsauth):
    """Create OpenSearch index with mapping."""
    
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
            print(f"Response: {json.dumps(response.json(), indent=2)}")
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
            print("\nThe role may not have the correct fine-grained permissions.")
            print("You may need to configure fine-grained access control permissions in OpenSearch Dashboards.")
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
    print("OpenSearch Index Setup (with Master User Role)")
    print("=" * 60)
    print(f"Endpoint: {OPENSEARCH_ENDPOINT}")
    print(f"Region: {REGION}")
    print(f"Index: {INDEX_NAME}")
    print("=" * 60)
    
    awsauth = None
    
    if MASTER_ROLE_ARN:
        awsauth = assume_role_and_create_index(MASTER_ROLE_ARN)
        if not awsauth:
            print("Failed to assume role. Exiting.")
            sys.exit(1)
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
    
    if create_index(awsauth):
        print("\n" + "=" * 60)
        print("Setup complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Setup failed. See error messages above.")
        print("\nAlternative: Create index via OpenSearch Dashboards:")
        print("1. Go to: https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards")
        print("2. Sign in with your IAM master user role")
        print("3. Go to Dev Tools")
        print("4. Run: PUT /photos with the mapping")
        print("=" * 60)
        sys.exit(1)

