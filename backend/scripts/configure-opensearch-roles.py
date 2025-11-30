#!/usr/bin/env python3
"""
Script to configure OpenSearch role mappings for fine-grained access control.
This grants the necessary permissions to create indices.
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import sys

OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
REGION = 'us-east-1'

def get_auth():
    """Get AWS credentials for authentication."""
    credentials = boto3.Session().get_credentials()
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        'es',
        session_token=credentials.token
    )

def create_all_access_role(awsauth):
    """Create or update a role with all_access permissions."""
    
    # First, check if all_access role exists
    url = f"https://{OPENSEARCH_ENDPOINT}/_plugins/_security/api/roles/all_access"
    
    try:
        response = requests.get(url, auth=awsauth, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print("✓ all_access role already exists")
        elif response.status_code == 404:
            print("Creating all_access role...")
            # Create the role
            role_url = f"https://{OPENSEARCH_ENDPOINT}/_plugins/_security/api/roles/all_access"
            role_config = {
                "cluster_permissions": ["cluster_all"],
                "index_permissions": [{
                    "index_patterns": ["*"],
                    "dls": "",
                    "fls": [],
                    "masked_fields": [],
                    "allowed_actions": ["*"]
                }]
            }
            response = requests.put(role_url, auth=awsauth, json=role_config, headers={"Content-Type": "application/json"})
            if response.status_code in [200, 201]:
                print("✓ Created all_access role")
            else:
                print(f"✗ Failed to create role: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Error checking/creating role: {e}")
        return False
    
    return True

def map_role_to_iam(awsauth, iam_arn):
    """Map IAM ARN to all_access role."""
    
    url = f"https://{OPENSEARCH_ENDPOINT}/_plugins/_security/api/rolesmapping/all_access"
    
    mapping = {
        "backend_roles": [iam_arn],
        "hosts": [],
        "users": []
    }
    
    print(f"Mapping IAM ARN {iam_arn} to all_access role...")
    
    try:
        # First check if mapping exists
        response = requests.get(url, auth=awsauth, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            # Update existing mapping
            existing = response.json()
            if iam_arn not in existing.get('backend_roles', []):
                existing['backend_roles'].append(iam_arn)
                response = requests.put(url, auth=awsauth, json=existing, headers={"Content-Type": "application/json"})
            else:
                print("✓ IAM ARN already mapped")
                return True
        else:
            # Create new mapping
            response = requests.put(url, auth=awsauth, json=mapping, headers={"Content-Type": "application/json"})
        
        if response.status_code in [200, 201]:
            print(f"✓ Successfully mapped {iam_arn} to all_access role")
            return True
        else:
            print(f"✗ Failed to map role: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error mapping role: {e}")
        return False

def main():
    print("=" * 60)
    print("OpenSearch Role Mapping Configuration")
    print("=" * 60)
    
    # Get account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    iam_arn = f"arn:aws:iam::{account_id}:root"
    
    print(f"Account ID: {account_id}")
    print(f"IAM ARN: {iam_arn}")
    print("=" * 60)
    
    awsauth = get_auth()
    
    # Create all_access role if needed
    if not create_all_access_role(awsauth):
        print("\nFailed to configure role. You may need to do this manually.")
        return False
    
    # Map IAM ARN to role
    if map_role_to_iam(awsauth, iam_arn):
        print("\n" + "=" * 60)
        print("✓ Role mapping configured successfully!")
        print("You can now create the index.")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("✗ Failed to configure role mapping.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    if main():
        print("\nNext step: Run setup-opensearch-index.py to create the index")
    else:
        sys.exit(1)

