#!/usr/bin/env python3
"""
Set OpenSearch master user via AWS CLI/SDK.
This bypasses the console issue where the master user ARN doesn't persist.
"""

import boto3
import json
import time
import sys

DOMAIN_NAME = 'photos'
REGION = 'us-east-1'
MASTER_ROLE_ARN = 'arn:aws:iam::837134650320:role/opensearch-master-role'

def set_master_user():
    """Set the master user for OpenSearch domain using SDK."""
    
    opensearch = boto3.client('opensearch', region_name=REGION)
    
    print("=" * 60)
    print("Setting OpenSearch Master User via AWS SDK")
    print("=" * 60)
    print(f"Domain: {DOMAIN_NAME}")
    print(f"Master User ARN: {MASTER_ROLE_ARN}")
    print("=" * 60)
    
    # Advanced security options with master user
    advanced_security_options = {
        'Enabled': True,
        'InternalUserDatabaseEnabled': False,
        'MasterUserOptions': {
            'MasterUserARN': MASTER_ROLE_ARN
        }
    }
    
    try:
        print("\nUpdating domain configuration...")
        response = opensearch.update_domain_config(
            DomainName=DOMAIN_NAME,
            AdvancedSecurityOptions=advanced_security_options
        )
        
        print("✓ Update initiated successfully!")
        print(f"\nDomain status: Processing")
        print("\nThis may take 5-10 minutes to complete.")
        print("Waiting for domain to become active...")
        
        # Wait for domain to be updated
        while True:
            time.sleep(30)
            status = opensearch.describe_domain(DomainName=DOMAIN_NAME)
            processing = status['Domain']['Processing']
            
            if not processing:
                print("\n✓ Domain update complete!")
                break
            else:
                print(".", end="", flush=True)
        
        # Verify the master user was set
        config = opensearch.describe_domain_config(DomainName=DOMAIN_NAME)
        master_options = config['DomainConfig'].get('AdvancedSecurityOptions', {}).get('Options', {})
        
        print("\n" + "=" * 60)
        print("✓ Master user configuration updated!")
        print("=" * 60)
        print(f"Advanced Security Enabled: {master_options.get('Enabled')}")
        print(f"Internal User Database: {master_options.get('InternalUserDatabaseEnabled')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    if set_master_user():
        print("\n✓ Master user set successfully!")
        print("\nNext step: Run setup-opensearch-index.py to create the index")
    else:
        print("\n✗ Failed to set master user")
        sys.exit(1)

