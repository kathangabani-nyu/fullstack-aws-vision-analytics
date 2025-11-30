#!/usr/bin/env python3
"""
Set OpenSearch master user using internal user database (username/password).
This is an alternative to IAM-based master user.
"""

import boto3
import time
import sys

DOMAIN_NAME = 'photos'
REGION = 'us-east-1'

# Master user credentials - use a strong password
MASTER_USERNAME = 'admin'
MASTER_PASSWORD = 'OpenSearch@Admin123!'  # Must meet password policy: uppercase, lowercase, number, special char

def set_master_user_internal():
    """Set master user using internal user database."""
    
    opensearch = boto3.client('opensearch', region_name=REGION)
    
    print("=" * 60)
    print("Setting OpenSearch Master User (Internal Database)")
    print("=" * 60)
    print(f"Domain: {DOMAIN_NAME}")
    print(f"Master Username: {MASTER_USERNAME}")
    print("=" * 60)
    
    # Advanced security options with internal user database
    advanced_security_options = {
        'Enabled': True,
        'InternalUserDatabaseEnabled': True,
        'MasterUserOptions': {
            'MasterUserName': MASTER_USERNAME,
            'MasterUserPassword': MASTER_PASSWORD
        }
    }
    
    try:
        print("\nUpdating domain configuration...")
        print("This will take 5-10 minutes...")
        
        response = opensearch.update_domain_config(
            DomainName=DOMAIN_NAME,
            AdvancedSecurityOptions=advanced_security_options
        )
        
        print("✓ Update initiated!")
        print("\nWaiting for domain to become active...")
        
        # Wait for domain to be updated
        wait_count = 0
        while True:
            time.sleep(30)
            wait_count += 1
            
            try:
                status = opensearch.describe_domain(DomainName=DOMAIN_NAME)
                processing = status['DomainStatus']['Processing']
                
                if not processing:
                    print("\n✓ Domain update complete!")
                    break
                else:
                    print(f"  Still processing... ({wait_count * 30}s elapsed)")
            except Exception as e:
                print(f"  Checking status... ({wait_count * 30}s elapsed)")
            
            if wait_count > 30:  # 15 minutes max
                print("\nTimeout waiting for domain. Check AWS Console for status.")
                break
        
        print("\n" + "=" * 60)
        print("✓ Master user configured!")
        print("=" * 60)
        print(f"\nMaster Username: {MASTER_USERNAME}")
        print(f"Master Password: {MASTER_PASSWORD}")
        print("\nSave these credentials - you'll need them to access OpenSearch!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("\nThis will set up a master user with username/password authentication.")
    print("This is more reliable than IAM-based master user.\n")
    
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    if set_master_user_internal():
        print("\n✓ Master user set successfully!")
        print("\nNext: Use these credentials to access OpenSearch Dashboards")
        print(f"URL: https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards")
    else:
        print("\n✗ Failed to set master user")
        sys.exit(1)

