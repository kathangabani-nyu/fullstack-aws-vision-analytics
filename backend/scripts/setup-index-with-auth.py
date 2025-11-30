#!/usr/bin/env python3
"""
Create OpenSearch index using master user credentials.
"""

import requests
import json
import sys

OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
INDEX_NAME = 'photos'

# Master user credentials
MASTER_USERNAME = 'admin'
MASTER_PASSWORD = 'OpenSearch@Admin123!'

def create_index():
    """Create OpenSearch index with mapping using basic auth."""
    
    print("=" * 60)
    print("OpenSearch Index Setup (with Master User Auth)")
    print("=" * 60)
    print(f"Endpoint: {OPENSEARCH_ENDPOINT}")
    print(f"Index: {INDEX_NAME}")
    print("=" * 60)
    
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
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    
    print(f"\nCreating index '{INDEX_NAME}'...")
    
    try:
        response = requests.put(
            url,
            auth=(MASTER_USERNAME, MASTER_PASSWORD),
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
        else:
            print(f"✗ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

def verify_index():
    """Verify the index was created."""
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{INDEX_NAME}"
    
    try:
        response = requests.get(
            url,
            auth=(MASTER_USERNAME, MASTER_PASSWORD),
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"\n✓ Index verification successful!")
            return True
        else:
            print(f"✗ Index verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False

if __name__ == "__main__":
    if create_index():
        verify_index()
        print("\n" + "=" * 60)
        print("✓ OpenSearch index setup complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Setup failed")
        print("=" * 60)
        sys.exit(1)

