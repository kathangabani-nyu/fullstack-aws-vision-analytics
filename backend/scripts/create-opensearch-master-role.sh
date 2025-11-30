#!/bin/bash

# Script to create IAM role for OpenSearch master user

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
ROLE_NAME="opensearch-master-role"

echo "Creating IAM role for OpenSearch master user..."

# Create trust policy
cat > /tmp/opensearch-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file:///tmp/opensearch-trust-policy.json \
  --region $REGION

# Attach OpenSearch access policy
cat > /tmp/opensearch-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:*"
      ],
      "Resource": "arn:aws:es:${REGION}:${ACCOUNT_ID}:domain/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name OpenSearchAccessPolicy \
  --policy-document file:///tmp/opensearch-policy.json \
  --region $REGION

echo ""
echo "IAM role created successfully!"
echo "Use this ARN as the OpenSearch master user:"
echo "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "Clean up temp files:"
echo "rm /tmp/opensearch-trust-policy.json /tmp/opensearch-policy.json"

