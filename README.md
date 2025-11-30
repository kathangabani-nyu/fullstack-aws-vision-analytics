# Photo Album Search Application

A serverless photo album web application with natural language search capabilities using AWS services.

## Architecture

- **Backend**: Python Lambda functions (index-photos, search-photos)
- **Frontend**: Vanilla JavaScript/HTML/CSS
- **Storage**: S3 buckets (B1: frontend, B2: photos)
- **Search**: Amazon OpenSearch Service (domain: "photos")
- **AI Services**: Rekognition (label detection), Lex (query disambiguation)
- **API**: API Gateway with S3 proxy and Lambda integration
- **CI/CD**: CodePipeline for both frontend and backend
- **Infrastructure**: CloudFormation template

## Project Structure

```
assignment-3/
├── backend/
│   ├── lambda/
│   │   ├── index-photos/
│   │   │   ├── lambda_function.py
│   │   │   └── requirements.txt
│   │   └── search-photos/
│   │       ├── lambda_function.py
│   │       └── requirements.txt
│   └── cloudformation/
│       └── template.yaml
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── buildspec.yml
└── README.md
```

## Setup Instructions

### Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured (region: us-east-1)
3. Python 3.9+ installed locally
4. GitHub repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics

### Step 1: Create OpenSearch Domain

1. Go to Amazon OpenSearch Service console
2. Create a new domain named "photos"
3. Instance type: t2.small.search (for cost optimization)
4. Configure access policy to allow Lambda functions access
5. Note the OpenSearch endpoint URL

### Step 2: Create Lex Bot

1. Go to Amazon Lex console
2. Create a new bot with intent "SearchIntent"
3. Add training utterances:
   - Keywords: "trees", "birds", "cats", "dogs"
   - Sentences: "show me trees", "show me photos with trees and birds", "find cats and dogs"
4. Build and publish the bot
5. Note the bot name and alias

### Step 3: Deploy CloudFormation Template

```bash
aws cloudformation create-stack \
  --stack-name photo-album-stack \
  --template-body file://backend/cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Step 4: Configure Lambda Functions

After CloudFormation deployment, update Lambda environment variables:

**index-photos Lambda:**
- `OPENSEARCH_ENDPOINT`: Your OpenSearch endpoint
- `OPENSEARCH_INDEX`: "photos"

**search-photos Lambda:**
- `OPENSEARCH_ENDPOINT`: Your OpenSearch endpoint
- `OPENSEARCH_INDEX`: "photos"
- `LEX_BOT_NAME`: Your Lex bot name
- `LEX_BOT_ALIAS`: Your Lex bot alias

### Step 5: Set Up S3 Event Trigger

1. Go to S3 bucket B2 (photos bucket)
2. Properties → Event notifications
3. Create event notification:
   - Event type: PUT
   - Destination: Lambda function (index-photos)

### Step 6: Configure API Gateway

1. Deploy the API
2. Create API key and associate with both methods
3. Generate JavaScript SDK
4. Download SDK and update frontend/app.js with SDK path

### Step 7: Deploy Frontend

1. Upload frontend files to S3 bucket B1
2. Enable static website hosting
3. Note the website URL

### Step 8: Set Up CodePipeline

**Backend Pipeline (P1):**
1. Create pipeline with GitHub source
2. Repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics
3. Branch: main (or your default branch)
4. Build provider: AWS CodeBuild
5. Deploy provider: AWS Lambda

**Frontend Pipeline (P2):**
1. Create pipeline with GitHub source
2. Repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics
3. Branch: main (or your default branch)
4. Build provider: AWS CodeBuild
5. Deploy provider: Amazon S3

## Testing

1. Upload a photo via the frontend
2. Check CloudWatch logs for index-photos Lambda
3. Verify photo is indexed in OpenSearch
4. Search for photos using natural language queries
5. Verify results are displayed correctly

## Custom Labels

When uploading photos, you can specify custom labels (comma-separated). These will be combined with Rekognition-detected labels and indexed in OpenSearch.

Example: "Sam, Sally, Birthday Party"

## API Endpoints

- **PUT /photos**: Upload a photo to S3
- **GET /search?q={query}**: Search photos using natural language

## Cost Optimization

- OpenSearch: t2.small.search instance
- Lambda: Appropriate timeout values (30s for index, 10s for search)
- S3: Standard storage class

## Troubleshooting

- Check CloudWatch logs for Lambda functions
- Verify IAM permissions for all services
- Ensure CORS is configured correctly
- Check API Gateway logs for API issues

## Author

Kathan Gabani (kdg7224)

