#!/usr/bin/env python3
"""
Update OpenSearch access policy to allow all actions.
Fine-grained access control will still protect the data.
"""

import boto3
import json
import time
import sys

DOMAIN_NAME = 'photos'
REGION = 'us-east-1'

def update_access_policy():
    """Update OpenSearch access policy to be more permissive."""
    
    opensearch = boto3.client('opensearch', region_name=REGION)
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    print("=" * 60)
    print("Updating OpenSearch Access Policy")
    print("=" * 60)
    print(f"Domain: {DOMAIN_NAME}")
    print(f"Account: {account_id}")
    print("=" * 60)
    
    # More permissive access policy
    # Fine-grained access control will still protect the data
    access_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "es:*",
                "Resource": f"arn:aws:es:{REGION}:{account_id}:domain/{DOMAIN_NAME}/*"
            }
        ]
    }
    
    policy_json = json.dumps(access_policy)
    
    print(f"\nAccess Policy:")
    print(json.dumps(access_policy, indent=2))
    
    try:
        print("\nUpdating access policy...")
        response = opensearch.update_domain_config(
            DomainName=DOMAIN_NAME,
            AccessPolicies=policy_json
        )
        
        print("✓ Update initiated!")
        print("\nWaiting for domain to become active...")
        
        # Wait for domain to be updated
        wait_count = 0
        while True:
            time.sleep(15)
            wait_count += 1
            
            try:
                status = opensearch.describe_domain(DomainName=DOMAIN_NAME)
                processing = status['DomainStatus']['Processing']
                
                if not processing:
                    print("\n✓ Domain update complete!")
                    break
                else:
                    print(f"  Still processing... ({wait_count * 15}s elapsed)")
            except Exception as e:
                print(f"  Checking status...")
            
            if wait_count > 20:  # 5 minutes max
                print("\nTimeout. Check AWS Console for status.")
                break
        
        print("\n" + "=" * 60)
        print("✓ Access policy updated!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    if update_access_policy():
        print("\n✓ Access policy updated successfully!")
        print("\nNext: Run setup-index-with-auth.py to create the index")
    else:
        print("\n✗ Failed to update access policy")
        sys.exit(1)

