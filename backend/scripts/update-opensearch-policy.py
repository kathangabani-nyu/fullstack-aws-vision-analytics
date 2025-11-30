#!/usr/bin/env python3
"""
Script to update OpenSearch domain access policy.
This allows your AWS account to access OpenSearch.
"""

import boto3
import json
import sys

DOMAIN_NAME = 'photos'
REGION = 'us-east-1'

def update_access_policy():
    """Update OpenSearch domain access policy."""
    
    # Get account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    print(f"Account ID: {account_id}")
    print(f"Domain: {DOMAIN_NAME}")
    print(f"Region: {REGION}")
    
    # Create access policy
    access_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "es:*",
                "Resource": f"arn:aws:es:{REGION}:{account_id}:domain/{DOMAIN_NAME}/*"
            }
        ]
    }
    
    policy_json = json.dumps(access_policy, indent=2)
    print(f"\nAccess Policy:")
    print(policy_json)
    
    # Update domain
    opensearch = boto3.client('opensearch', region_name=REGION)
    
    try:
        print(f"\nUpdating access policy for domain '{DOMAIN_NAME}'...")
        response = opensearch.update_domain_config(
            DomainName=DOMAIN_NAME,
            AccessPolicies=policy_json
        )
        
        print("✓ Policy updated successfully!")
        print(f"\nDomain Status: {response['DomainConfig']['ClusterConfig']['Status']['Value']}")
        print("\nNote: It may take 2-3 minutes for the policy changes to propagate.")
        print("After waiting, try creating the index again.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error updating policy: {e}")
        print("\nAlternative: Update via AWS Console:")
        print("1. Go to OpenSearch Service Console")
        print(f"2. Select domain: {DOMAIN_NAME}")
        print("3. Go to Security tab")
        print("4. Click 'Edit' on Access policy")
        print("5. Paste the policy shown above")
        print("6. Click 'Save changes'")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenSearch Access Policy Update")
    print("=" * 60)
    
    if update_access_policy():
        print("\n" + "=" * 60)
        print("Policy update initiated. Wait 2-3 minutes, then create the index.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Failed to update policy. See instructions above.")
        print("=" * 60)
        sys.exit(1)

