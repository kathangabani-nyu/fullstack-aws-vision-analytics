#!/usr/bin/env python3
"""
Create IAM role for OpenSearch master user.
"""

import boto3
import json
import sys

ROLE_NAME = 'opensearch-master-role'
REGION = 'us-east-1'

def create_role():
    """Create IAM role for OpenSearch master user."""
    
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    print("=" * 60)
    print("Creating IAM Role for OpenSearch Master User")
    print("=" * 60)
    print(f"Account ID: {account_id}")
    print(f"Role Name: {ROLE_NAME}")
    print("=" * 60)
    
    # Trust policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Create role
    try:
        print("\nCreating IAM role...")
        response = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='IAM role for OpenSearch master user'
        )
        print(f"✓ Role created: {response['Role']['Arn']}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"⚠ Role {ROLE_NAME} already exists")
        response = iam.get_role(RoleName=ROLE_NAME)
        print(f"Using existing role: {response['Role']['Arn']}")
    except Exception as e:
        print(f"✗ Error creating role: {e}")
        return None
    
    role_arn = response['Role']['Arn']
    
    # Create policy
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "es:*"
                ],
                "Resource": f"arn:aws:es:{REGION}:{account_id}:domain/*"
            }
        ]
    }
    
    # Attach policy
    try:
        print("\nAttaching policy to role...")
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName='OpenSearchAccessPolicy',
            PolicyDocument=json.dumps(policy)
        )
        print("✓ Policy attached successfully")
    except Exception as e:
        print(f"✗ Error attaching policy: {e}")
        return None
    
    print("\n" + "=" * 60)
    print("✓ IAM role created successfully!")
    print("=" * 60)
    print(f"\nRole ARN: {role_arn}")
    print("\nNext steps:")
    print("1. Go to OpenSearch Console → photos domain → Security tab")
    print("2. Click 'Edit' on 'Fine-grained access control'")
    print("3. Under 'Master user', select 'Set IAM ARN as master user'")
    print(f"4. Enter this ARN: {role_arn}")
    print("5. Click 'Save changes'")
    print("6. Wait 2-3 minutes for changes to propagate")
    print("7. Then we can create the index")
    print("=" * 60)
    
    return role_arn

if __name__ == "__main__":
    role_arn = create_role()
    if role_arn:
        print(f"\n✓ Use this ARN in OpenSearch Console: {role_arn}")
    else:
        sys.exit(1)

