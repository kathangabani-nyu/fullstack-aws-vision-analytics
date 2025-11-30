#!/bin/bash

# Script to update OpenSearch access policy
# This allows your account to access OpenSearch

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
DOMAIN_NAME="photos"

echo "Updating OpenSearch access policy for account: $ACCOUNT_ID"

# Create access policy
cat > /tmp/opensearch-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:${REGION}:${ACCOUNT_ID}:domain/${DOMAIN_NAME}/*"
    }
  ]
}
EOF

echo "Policy to apply:"
cat /tmp/opensearch-policy.json

echo ""
echo "Updating OpenSearch domain access policy..."
aws opensearch update-domain-config \
  --domain-name $DOMAIN_NAME \
  --access-policies file:///tmp/opensearch-policy.json \
  --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ Policy updated successfully!"
    echo "Wait 2-3 minutes for changes to propagate, then try creating the index again."
else
    echo "✗ Failed to update policy. Try updating via AWS Console:"
    echo "  1. Go to OpenSearch Console"
    echo "  2. Select domain: $DOMAIN_NAME"
    echo "  3. Security tab → Edit access policy"
    echo "  4. Paste the policy from /tmp/opensearch-policy.json"
fi

