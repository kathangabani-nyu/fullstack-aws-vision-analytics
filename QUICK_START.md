# Quick Start Guide

This is a condensed guide to get you started quickly. For detailed instructions, see `SETUP.md` and the `docs/` folder.

## Prerequisites Checklist

- [ ] AWS Account with CLI configured (us-east-1)
- [ ] Python 3.9+ installed
- [ ] GitHub repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics

## Quick Setup Steps

### 1. Create OpenSearch Domain (10-15 min)

```bash
# Use AWS Console or CLI
# Domain name: photos
# Instance: t2.small.search
# See docs/OPENSEARCH_SETUP.md for details
```

After creation, note the endpoint URL.

### 2. Create Lex Bot (5 min)

```bash
# Use AWS Console
# Bot name: PhotoSearchBot
# Intent: SearchIntent
# See docs/LEX_SETUP.md for details
```

After creation, note Bot ID and Alias ID.

### 3. Package Lambda Functions

```bash
cd backend
chmod +x scripts/package-lambdas.sh
./scripts/package-lambdas.sh
```

This creates `index-photos.zip` and `search-photos.zip` in the root directory.

### 4. Deploy CloudFormation Stack

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

Wait for stack creation (~5-10 minutes).

### 5. Update Lambda Functions with Dependencies

```bash
chmod +x backend/scripts/update-lambdas.sh
cd backend
./scripts/update-lambdas.sh
```

### 6. Configure S3 Event Trigger

1. Go to S3 Console
2. Open photos bucket (from CloudFormation outputs)
3. Properties → Event notifications → Create
4. Event: PUT → Destination: Lambda (index-photos)

### 7. Get API Key and Configure Frontend

1. API Gateway Console → Your API → API Keys
2. Copy API key value
3. Get API Gateway URL from CloudFormation outputs
4. Update `frontend/app.js`:
   ```javascript
   const API_CONFIG = {
       apiKey: 'YOUR_API_KEY',
       endpoint: 'YOUR_API_GATEWAY_URL',
       region: 'us-east-1'
   };
   ```

### 8. Generate and Include API Gateway SDK

1. API Gateway Console → Stages → prod → SDK Generation
2. Platform: JavaScript
3. Download and extract
4. Copy `lib/apigClient.js` to `frontend/lib/`
5. Update `frontend/index.html`:
   ```html
   <script src="lib/apigClient.js"></script>
   ```

### 9. Deploy Frontend

```bash
aws s3 sync frontend/ s3://YOUR_FRONTEND_BUCKET_NAME/ --delete
```

Get bucket name from CloudFormation outputs.

### 10. Create OpenSearch Index

**Option 1: Using Python Script (Recommended)**
```bash
# Update OPENSEARCH_ENDPOINT in backend/scripts/setup-opensearch-index.py
# Then run:
cd backend/scripts
pip install requests requests-aws4auth boto3
python setup-opensearch-index.py
```

**Option 2: Using OpenSearch Dashboards**
1. Go to: `https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards`
2. Sign in → Dev Tools
3. Run: `PUT /photos` with the mapping (see docs/OPENSEARCH_SETUP.md)

### 11. Test the Application

1. Visit frontend URL (from CloudFormation outputs)
2. Upload a photo with custom labels
3. Wait a few seconds for indexing
4. Search for photos using natural language

## CodePipeline Setup (Optional)

See `docs/CODEPIPELINE_SETUP.md` for automated deployment setup.

## Important Notes

1. **Lambda Dependencies**: The CloudFormation template includes inline code, but Lambda functions need to be updated with packaged dependencies (step 5).

2. **OpenSearch Index**: Must be created manually after domain creation (step 10).

3. **API Gateway SDK**: Must be generated and included in frontend (step 8).

4. **Costs**: 
   - OpenSearch: ~$15-20/month (t2.small.search)
   - Lambda: Pay per invocation (very low)
   - S3: Pay per storage/requests (very low)
   - API Gateway: Pay per request (very low)

## Troubleshooting

- **Lambda not triggered**: Check S3 event notification and Lambda permissions
- **Indexing fails**: Check OpenSearch endpoint and IAM permissions
- **Search returns nothing**: Verify index exists and documents are indexed
- **Frontend errors**: Check browser console and API key configuration

## Next Steps

- Set up CodePipeline for automated deployments
- Add more training utterances to Lex bot
- Monitor CloudWatch logs for errors
- Test with various photo types and search queries

## Cleanup

To avoid ongoing costs:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name photo-album-stack --region us-east-1

# Manually delete:
# - OpenSearch domain
# - Lex bot
# - CodePipeline projects (if created)
```

