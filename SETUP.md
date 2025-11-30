# Setup Instructions

This document provides step-by-step instructions for setting up the Photo Album Search Application.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured (region: us-east-1)
3. Python 3.9+ installed locally
4. GitHub repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics

## Step 1: Create OpenSearch Domain

1. Go to Amazon OpenSearch Service console: https://console.aws.amazon.com/es/
2. Click "Create domain"
3. Configure:
   - **Domain name**: `photos`
   - **Instance type**: `t2.small.search` (for cost optimization)
   - **Number of instances**: 1
   - **Storage**: 10 GB (EBS)
   - **Access policy**: Use the following policy to allow Lambda access:

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

4. Click "Create"
5. Wait for domain to be created (takes ~10-15 minutes)
6. Note the **endpoint URL** (e.g., `search-photos-xxxxx.us-east-1.es.amazonaws.com`)

### Create OpenSearch Index

After the domain is created, create the index mapping. **Use the Python script** (recommended):

```bash
# Install dependencies if needed
pip install requests requests-aws4auth boto3

# Update the endpoint in the script first, then run:
cd backend/scripts
python setup-opensearch-index.py
```

**Or use OpenSearch Dashboards:**
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

See `docs/OPENSEARCH_SETUP.md` for detailed instructions.

## Step 2: Create Amazon Lex Bot

1. Go to Amazon Lex console: https://console.aws.amazon.com/lex/
2. Click "Create" → "Custom bot"
3. Configure:
   - **Bot name**: `PhotoSearchBot`
   - **Language**: English (US)
   - **Output voice**: None (text only)
   - **Session timeout**: 5 minutes
   - **Sentiment analysis**: No
4. Click "Create"

### Create SearchIntent

1. In the bot editor, click "Add intent" → "Create new intent"
2. **Intent name**: `SearchIntent`
3. **Sample utterances** (add these):
   - `trees`
   - `birds`
   - `cats`
   - `dogs`
   - `show me trees`
   - `show me photos with trees`
   - `show me trees and birds`
   - `find cats and dogs`
   - `photos with trees`
   - `pictures of dogs`

4. **Slots** (optional - for structured extraction):
   - You can create slots for keywords, but the Lambda will handle flexible extraction

5. Click "Save intent"
6. Click "Build" (top right)
7. Wait for build to complete
8. Click "Publish" → Create new alias: `PROD`
9. Note the **Bot ID** and **Bot Alias ID** from the bot details

## Step 3: Package Lambda Functions

The CloudFormation template includes inline Lambda code, but you need to package the functions with dependencies for proper execution.

### Package index-photos Lambda

```bash
cd backend/lambda/index-photos
pip install -r requirements.txt -t .
zip -r ../../../index-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*"
cd ../../..
```

### Package search-photos Lambda

```bash
cd backend/lambda/search-photos
pip install -r requirements.txt -t .
zip -r ../../../search-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*"
cd ../../..
```

### Upload to S3 (for CloudFormation)

```bash
aws s3 cp index-photos.zip s3://YOUR_DEPLOYMENT_BUCKET/
aws s3 cp search-photos.zip s3://YOUR_DEPLOYMENT_BUCKET/
```

**Note**: Alternatively, you can update the Lambda functions directly after CloudFormation deployment using the packaged ZIP files.

## Step 4: Deploy CloudFormation Template

1. Update the CloudFormation template parameters with your OpenSearch endpoint and Lex bot details
2. Deploy the stack:

```bash
aws cloudformation create-stack \
  --stack-name photo-album-stack \
  --template-body file://backend/cloudformation/template.yaml \
  --parameters \
    ParameterKey=OpenSearchEndpoint,ParameterValue=YOUR_OPENSEARCH_ENDPOINT \
    ParameterKey=LexBotId,ParameterValue=YOUR_LEX_BOT_ID \
    ParameterKey=LexBotAliasId,ParameterValue=YOUR_LEX_BOT_ALIAS_ID \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

3. Wait for stack creation to complete (~5-10 minutes)
4. Note the outputs:
   - FrontendWebsiteURL
   - ApiGatewayURL
   - ApiKeyId

## Step 5: Update Lambda Functions with Dependencies

After CloudFormation deployment, update the Lambda functions with the packaged code:

```bash
# Update index-photos Lambda
aws lambda update-function-code \
  --function-name index-photos \
  --zip-file fileb://index-photos.zip \
  --region us-east-1

# Update search-photos Lambda
aws lambda update-function-code \
  --function-name search-photos \
  --zip-file fileb://search-photos.zip \
  --region us-east-1
```

## Step 6: Configure S3 Event Trigger

1. Go to S3 console: https://console.aws.amazon.com/s3/
2. Open the photos bucket (named: `photo-album-stack-photos-bucket`)
3. Go to Properties → Event notifications
4. Click "Create event notification"
5. Configure:
   - **Event name**: `TriggerIndexPhotos`
   - **Prefix**: (leave empty or use a prefix like `photos/`)
   - **Suffix**: (leave empty)
   - **Event types**: Select "PUT"
   - **Destination**: Lambda function → `index-photos`
6. Click "Save changes"

## Step 7: Get API Key

1. Go to API Gateway console: https://console.aws.amazon.com/apigateway/
2. Select your API
3. Go to "API Keys"
4. Find your API key and click on it
5. Click "Show" to reveal the API key value
6. Copy the API key value

## Step 8: Generate API Gateway SDK

1. In API Gateway console, select your API
2. Go to "Stages" → `prod`
3. Click "SDK Generation"
4. Select:
   - **Platform**: JavaScript
   - **Service name**: PhotoAlbumAPI
5. Click "Generate SDK"
6. Download and extract the SDK
7. Copy the `lib` folder to your frontend directory

## Step 9: Configure Frontend

1. Update `frontend/app.js` with your API configuration:

```javascript
const API_CONFIG = {
    apiKey: 'YOUR_API_KEY_HERE',
    endpoint: 'YOUR_API_GATEWAY_URL_HERE',
    region: 'us-east-1'
};
```

2. Include the API Gateway SDK in `frontend/index.html`:

```html
<script src="lib/apigClient.js"></script>
```

## Step 10: Deploy Frontend

1. Upload frontend files to S3 bucket B1:

```bash
aws s3 sync frontend/ s3://photo-album-stack-frontend-bucket/ --delete
```

2. The frontend should be accessible at the URL from CloudFormation outputs

## Step 11: Set Up CodePipeline

### Backend Pipeline (P1)

1. Go to CodePipeline console: https://console.aws.amazon.com/codesuite/codepipeline/
2. Click "Create pipeline"
3. Configure:
   - **Pipeline name**: `photo-album-backend-pipeline`
   - **Source**: GitHub (connect your repository)
     - Repository: `kathangabani-nyu/fullstack-aws-vision-analytics`
     - Branch: `main` (or your default branch)
     - Build provider: AWS CodeBuild
     - Project: Create new project
       - Environment: Managed image, Ubuntu, Standard, aws/codebuild/standard:5.0
       - Buildspec: `backend/buildspec.yml`
   - **Deploy**: AWS Lambda
     - Function name: `index-photos` and `search-photos`
     - Artifact: Use build artifacts

### Frontend Pipeline (P2)

1. Create another pipeline: `photo-album-frontend-pipeline`
2. Configure:
   - **Source**: GitHub (same repository)
   - **Build**: CodeBuild
     - Buildspec: `frontend/buildspec.yml`
     - Environment variable: `FRONTEND_BUCKET_NAME` = your frontend bucket name
   - **Deploy**: Amazon S3
     - Bucket: Your frontend bucket (B1)

## Testing

1. **Test Photo Upload**:
   - Go to the frontend website
   - Upload a photo with custom labels (e.g., "Sam, Sally")
   - Check CloudWatch logs for `index-photos` Lambda
   - Verify the photo appears in OpenSearch

2. **Test Search**:
   - Search for photos using natural language (e.g., "show me trees")
   - Verify results are displayed correctly
   - Test with custom labels

3. **Verify Custom Labels**:
   - Upload a photo with custom labels
   - Search for those custom labels
   - Verify the photo appears in results

## Troubleshooting

### Lambda function not triggered by S3
- Check S3 event notification configuration
- Verify Lambda permissions allow S3 to invoke
- Check CloudWatch logs for errors

### OpenSearch indexing fails
- Verify OpenSearch endpoint is correct
- Check IAM permissions for Lambda to access OpenSearch
- Verify index exists and mapping is correct

### Lex bot not extracting keywords
- Check Lex bot is built and published
- Verify bot ID and alias ID are correct
- Check CloudWatch logs for Lex responses

### API Gateway errors
- Verify API key is included in requests
- Check CORS configuration
- Verify Lambda permissions for API Gateway

### Frontend not loading
- Check S3 bucket static website hosting is enabled
- Verify bucket policy allows public read access
- Check CORS configuration on S3 bucket

## Cost Optimization Tips

1. Use t2.small.search for OpenSearch (smallest instance)
2. Set appropriate Lambda timeouts
3. Use S3 lifecycle policies for old photos
4. Monitor usage and adjust resources accordingly

## Cleanup

To avoid ongoing costs, delete the CloudFormation stack:

```bash
aws cloudformation delete-stack --stack-name photo-album-stack --region us-east-1
```

Also manually delete:
- OpenSearch domain
- Lex bot
- CodePipeline projects

