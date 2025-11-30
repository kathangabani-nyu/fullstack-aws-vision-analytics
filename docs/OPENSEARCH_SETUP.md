# Amazon OpenSearch Service Setup Guide

This guide provides detailed instructions for creating and configuring the OpenSearch domain.

## Step 1: Create OpenSearch Domain

1. Navigate to Amazon OpenSearch Service Console: https://console.aws.amazon.com/es/
2. Click "Create domain"
3. Configure the domain:

### Domain Configuration
- **Domain name**: `photos`
- **Deployment type**: Development and testing (single Availability Zone)
- **Version**: Latest (e.g., OpenSearch 2.3 or Elasticsearch 7.10)

### Cluster Configuration
- **Instance type**: `t2.small.search` (for cost optimization)
- **Number of instances**: 1
- **Dedicated master nodes**: Disable (not needed for small deployment)

### Storage Configuration
- **EBS volume type**: General Purpose (SSD) - gp3
- **EBS volume size**: 10 GB (minimum)
- **Encryption**: Optional (enable for production)

### Network Configuration
- **Network type**: VPC access (recommended) or Public access
  - For simplicity, you can use Public access with fine-grained access control
  - For VPC: Select your VPC and subnets

### Access Policy

Choose "Fine-grained access control" and configure:

**Option 1: Public Access with IAM (Recommended for this assignment)**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/photos/*"
    }
  ]
}
```

**Option 2: Fine-grained Access Control**
- Enable fine-grained access control
- Create a master user (or use IAM)
- Configure domain access policy to allow Lambda functions

4. Click "Create"
5. Wait for domain creation (takes 10-15 minutes)

## Step 2: Get Domain Endpoint

1. Once the domain is active, click on the domain name
2. Note the **Domain endpoint (IPv4)** URL 
   - Example: `search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com`
   - **Use this endpoint for Lambda functions** (not the dual stack or Dashboards URL)
3. This endpoint is needed for Lambda environment variables

**Important**: For Lambda functions, use only the hostname part (without `https://`):
- ✅ Correct: `search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com`
- ❌ Wrong: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com`

## Step 3: Create Index Mapping

After the domain is created, create the index with proper mapping. Since you're using fine-grained access control with IAM, you need to use AWS Signature Version 4 authentication.

### Your OpenSearch Endpoint

Based on your domain, use one of these endpoints:
- **Domain endpoint (IPv4)**: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com`
- **Domain endpoint v2 (dual stack)**: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws`

**For Lambda functions and scripts, use the IPv4 endpoint:**
```
search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com
```

### Method 1: Using Python Script (Recommended)

Create a script `setup-opensearch-index.py`:

```python
import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

# Your OpenSearch endpoint (use the IPv4 endpoint)
OPENSEARCH_ENDPOINT = "search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"
REGION = 'us-east-1'

# Get AWS credentials from your current session
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    'es',
    session_token=credentials.token
)

# Create index with mapping
url = f"https://{OPENSEARCH_ENDPOINT}/photos"
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

print(f"Creating index at: {url}")
response = requests.put(
    url,
    auth=awsauth,
    json=mapping,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
if response.status_code in [200, 201]:
    print("✓ Index created successfully!")
else:
    print(f"✗ Error: {response.text}")
```

**Run it:**
```bash
# Make sure you have requests and requests-aws4auth installed
pip install requests requests-aws4auth boto3

python setup-opensearch-index.py
```

### Method 2: Using AWS CLI with curl (Alternative)

If you have AWS CLI configured, you can use curl with AWS SigV4:

```bash
# Set your endpoint
ENDPOINT="search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"

# Create index
curl -X PUT "https://${ENDPOINT}/photos" \
  -H 'Content-Type: application/json' \
  --aws-sigv4 "aws:amz:us-east-1:es" \
  -d '{
    "mappings": {
      "properties": {
        "objectKey": { "type": "keyword" },
        "bucket": { "type": "keyword" },
        "createdTimestamp": { "type": "date" },
        "labels": { "type": "keyword" }
      }
    }
  }'
```

**Note**: This requires curl to support `--aws-sigv4` flag (available in newer versions).

### Method 3: Using OpenSearch Dashboards (Easiest)

1. Go to your OpenSearch Dashboards URL:
   ```
   https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards
   ```

2. Sign in using your IAM credentials (the master user role you configured)

3. Go to **Dev Tools** (left sidebar)

4. In the console, run:
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

5. Click the play button (▶) to execute

6. You should see a success response with `"acknowledged": true`

## Step 4: Verify Index Creation

### Using Python Script

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

# Check if index exists
url = f"https://{OPENSEARCH_ENDPOINT}/photos"
response = requests.get(url, auth=awsauth)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("✓ Index exists!")
    print(response.json())
else:
    print(f"✗ Index not found: {response.text}")
```

### Using OpenSearch Dashboards

1. Go to: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards`
2. Sign in
3. Go to **Dev Tools**
4. Run: `GET /photos`
5. You should see the index mapping

### Check Index Count

```python
# Get document count
url = f"https://{OPENSEARCH_ENDPOINT}/photos/_count"
response = requests.get(url, auth=awsauth)
print(f"Document count: {response.json()['count']}")
```

## Step 5: Update Lambda Environment Variables

Update both Lambda functions with the OpenSearch endpoint. **Use only the hostname (no https://)**:

```bash
# Your endpoint (hostname only, no protocol)
OPENSEARCH_ENDPOINT="search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"

# Update index-photos Lambda
aws lambda update-function-configuration \
  --function-name index-photos \
  --environment Variables="{OPENSEARCH_ENDPOINT=${OPENSEARCH_ENDPOINT},OPENSEARCH_INDEX=photos,AWS_REGION=us-east-1}" \
  --region us-east-1

# Update search-photos Lambda
aws lambda update-function-configuration \
  --function-name search-photos \
  --environment Variables="{OPENSEARCH_ENDPOINT=${OPENSEARCH_ENDPOINT},OPENSEARCH_INDEX=photos,AWS_REGION=us-east-1}" \
  --region us-east-1
```

**Or update via AWS Console:**
1. Go to Lambda Console
2. Select `index-photos` function
3. Configuration → Environment variables
4. Update `OPENSEARCH_ENDPOINT` with: `search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com`
5. Repeat for `search-photos` function

## Step 6: Test Indexing

1. Upload a photo via the frontend
2. Check CloudWatch logs for `index-photos` Lambda
3. Verify the document was indexed using Python:

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

# Search all documents
url = f"https://{OPENSEARCH_ENDPOINT}/photos/_search"
query = {"query": {"match_all": {}}}

response = requests.post(url, auth=awsauth, json=query, headers={"Content-Type": "application/json"})
print(f"Status: {response.status_code}")
print(f"Results: {response.json()}")
```

**Or use OpenSearch Dashboards:**
1. Go to Dev Tools
2. Run: `GET /photos/_search`
3. You should see indexed documents

## Cost Optimization

- Use `t2.small.search` instance type (smallest available)
- Single Availability Zone deployment
- 10 GB EBS volume (minimum)
- Monitor usage and delete when not needed

## Security Best Practices

1. **Use VPC**: Deploy in VPC for better security
2. **Fine-grained access control**: Enable and use IAM roles
3. **Encryption**: Enable encryption at rest
4. **HTTPS only**: Ensure all connections use HTTPS
5. **Access policies**: Restrict access to specific IAM roles/users

## Troubleshooting

### Cannot connect to OpenSearch
- Check security group rules (if using VPC)
- Verify access policy allows your Lambda role
- Check endpoint URL is correct

### Indexing fails
- Verify index exists
- Check IAM permissions for Lambda
- Verify endpoint URL in environment variables
- Check CloudWatch logs for detailed errors

### Search returns no results
- Verify documents are indexed (check index count)
- Check search query syntax
- Verify labels are indexed correctly

## Cleanup

To avoid ongoing costs:

```bash
aws es delete-elasticsearch-domain --domain-name photos --region us-east-1
```

Note: This action cannot be undone and all data will be lost.

