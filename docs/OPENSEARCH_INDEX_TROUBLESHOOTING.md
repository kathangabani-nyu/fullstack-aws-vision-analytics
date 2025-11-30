# OpenSearch Index Creation Troubleshooting

## Issue: Authentication Failed / Permission Denied (403)

If you're getting a 403 error when trying to create the index, it's because fine-grained access control requires using the IAM role that was set as the master user.

## Solution 1: Update OpenSearch Access Policy (Recommended)

Update your OpenSearch domain access policy to allow your current user/role:

1. Go to OpenSearch Service Console
2. Click on your domain `photos`
3. Go to **Security** tab
4. Click **Edit** on Access policy
5. Update the policy to allow your account or specific role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::837134650320:root"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:837134650320:domain/photos/*"
    }
  ]
}
```

6. Click **Save changes**
7. Wait a few minutes for the policy to propagate
8. Try running the script again

## Solution 2: Use the Master User Role

If you set a specific IAM role as the master user, you need to use that role:

1. **Find the role ARN** you used when creating OpenSearch:
   - Go to OpenSearch Console → Your domain → Security
   - Check the "Fine-grained access control" section
   - Note the IAM ARN

2. **Assume the role and run the script:**
   ```bash
   # Get temporary credentials
   aws sts assume-role \
     --role-arn "arn:aws:iam::837134650320:role/YOUR_MASTER_ROLE" \
     --role-session-name "opensearch-setup" \
     > role-credentials.json
   
   # Export credentials
   export AWS_ACCESS_KEY_ID=$(cat role-credentials.json | jq -r '.Credentials.AccessKeyId')
   export AWS_SECRET_ACCESS_KEY=$(cat role-credentials.json | jq -r '.Credentials.SecretAccessKey')
   export AWS_SESSION_TOKEN=$(cat role-credentials.json | jq -r '.Credentials.SessionToken')
   
   # Run the script
   python backend/scripts/setup-opensearch-index.py
   ```

## Solution 3: Create Index via AWS CLI (If Policy Allows)

If your access policy allows it, you can try using AWS CLI:

```bash
# This might work if the policy is permissive enough
aws es create-elasticsearch-index \
  --domain-name photos \
  --index-name photos \
  --region us-east-1
```

## Solution 4: Use OpenSearch Dashboards (If You Can Access)

If you can access Dashboards:

1. Go to: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards`
2. Sign in with your IAM credentials
3. Go to **Dev Tools**
4. Run:
   ```json
   PUT /photos
   {
     "mappings": {
       "properties": {
         "objectKey": { "type": "keyword" },
         "bucket": { "type": "keyword" },
         "createdTimestamp": { "type": "date" },
         "labels": { "type": "keyword" }
       }
     }
   }
   ```

## Quick Fix: Update Access Policy

The easiest solution is to update the OpenSearch access policy to allow your account:

```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create policy file
cat > opensearch-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:${ACCOUNT_ID}:domain/photos/*"
    }
  ]
}
EOF

# Update the policy (via AWS Console is easier)
# Go to OpenSearch Console → photos domain → Security → Edit access policy
# Paste the JSON above
```

After updating the policy, wait 2-3 minutes and try the script again.

## Verify Access

Test if you can access OpenSearch:

```python
import boto3
import requests
from requests_aws4auth import AWS4Auth

OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
REGION = 'us-east-1'

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    'es',
    session_token=credentials.token
)

# Test access
url = f"https://{OPENSEARCH_ENDPOINT}/"
response = requests.get(url, auth=awsauth)
print(f"Status: {response.status_code}")
print(response.json())
```

If this returns 200, you have access. If 403, update the access policy.

