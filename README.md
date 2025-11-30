# Photo Album Web Application

A serverless photo album application with natural language search capabilities, built on AWS.

## Architecture

```
Frontend (S3) --> API Gateway --> Lambda (search-photos) --> Amazon Lex
                      |                    |
                      |                    v
                      |              OpenSearch
                      |                    ^
                      v                    |
                Photos S3 --> Lambda (index-photos) --> Rekognition
```

## Components

| Component | AWS Service | Description |
|-----------|-------------|-------------|
| Frontend (B1) | S3 Static Website | Web interface for search and upload |
| Photos Storage (B2) | S3 Bucket | Stores uploaded photos |
| Index Lambda (LF1) | Lambda | Indexes photos using Rekognition labels |
| Search Lambda (LF2) | Lambda | Handles natural language search queries |
| Search Bot | Amazon Lex | Extracts keywords from natural language |
| Photo Index | OpenSearch | Stores searchable photo metadata |
| API | API Gateway | REST API with S3 proxy for uploads |
| CI/CD | CodePipeline | Automated deployments from GitHub |

## Features

- Upload photos with custom labels via web interface
- Automatic object detection using AWS Rekognition
- Natural language search (e.g., "show me cats and dogs")
- Custom label support via `x-amz-meta-customLabels` header
- Keyword extraction using Amazon Lex
- Full-text search across all detected and custom labels

## Project Structure

```
.
├── backend/
│   ├── cloudformation/
│   │   └── template.yaml          # CloudFormation infrastructure template
│   ├── lambda/
│   │   ├── index-photos/
│   │   │   └── lambda_function.py # Photo indexing Lambda (LF1)
│   │   └── search-photos/
│   │       └── lambda_function.py # Photo search Lambda (LF2)
│   ├── scripts/                   # Deployment and setup scripts
│   └── buildspec.yml              # CodeBuild specification for backend
├── frontend/
│   ├── index.html                 # Main HTML page
│   ├── styles.css                 # Stylesheet
│   ├── app.js                     # Frontend JavaScript
│   └── buildspec.yml              # CodeBuild specification for frontend
└── README.md
```

## API Endpoints

### PUT /photos/{filename}
Upload a photo to the album.

**Headers:**
- `x-api-key`: API key (required)
- `Content-Type`: Image MIME type
- `x-amz-meta-customLabels`: Comma-separated custom labels (optional)

**Example:**
```bash
curl -X PUT "https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/photos/my-photo.jpg" \
  -H "x-api-key: {api-key}" \
  -H "Content-Type: image/jpeg" \
  -H "x-amz-meta-customLabels: vacation, beach" \
  --data-binary @my-photo.jpg
```

### GET /search?q={query}
Search for photos using natural language.

**Parameters:**
- `q`: Search query (e.g., "show me dogs", "cats and birds")

**Response:**
```json
[
  {
    "objectKey": "photo.jpg",
    "bucket": "photos-bucket",
    "createdTimestamp": "2024-11-30T12:00:00",
    "labels": ["dog", "pet", "animal"]
  }
]
```

## Deployment

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.9+
- GitHub repository connected to AWS CodePipeline

### CloudFormation Deployment
```bash
aws cloudformation create-stack \
  --stack-name photo-album-stack \
  --template-body file://backend/cloudformation/template.yaml \
  --capabilities CAPABILITY_IAM
```

### Manual Setup Required
1. **OpenSearch Domain**: Create domain "photos" with fine-grained access control
2. **Lex Bot**: Create "PhotoSearchBot" with SearchIntent
3. **CodePipeline**: Connect GitHub repository for CI/CD

## OpenSearch Index Schema

```json
{
  "objectKey": "string",
  "bucket": "string", 
  "createdTimestamp": "datetime",
  "labels": ["string"]
}
```

## Lambda Environment Variables

### index-photos
| Variable | Description |
|----------|-------------|
| OPENSEARCH_ENDPOINT | OpenSearch domain endpoint |
| OPENSEARCH_INDEX | Index name (default: photos) |
| OPENSEARCH_USERNAME | Master user username |
| OPENSEARCH_PASSWORD | Master user password |

### search-photos
| Variable | Description |
|----------|-------------|
| OPENSEARCH_ENDPOINT | OpenSearch domain endpoint |
| OPENSEARCH_INDEX | Index name (default: photos) |
| OPENSEARCH_USERNAME | Master user username |
| OPENSEARCH_PASSWORD | Master user password |
| LEX_BOT_ID | Lex bot identifier |
| LEX_BOT_ALIAS_ID | Lex bot alias identifier |

## Lex Bot Configuration

**Bot Name:** PhotoSearchBot

**Intent:** SearchIntent

**Sample Utterances:**
- `{keyword1}`
- `show me {keyword1}`
- `find {keyword1}`
- `{keyword1} and {keyword2}`
- `show me {keyword1} and {keyword2}`
- `photos of {keyword1}`

**Slots:**
- `keyword1` (AMAZON.AlphaNumeric) - Primary search term
- `keyword2` (AMAZON.AlphaNumeric) - Secondary search term

## Testing

### Search Examples
```
cat                     -> Returns all photos with cats
show me dogs            -> Returns all photos with dogs  
cats and dogs           -> Returns photos with cats OR dogs
show me farm animals    -> Returns farm animal photos
```

### Upload Test
1. Navigate to the frontend URL
2. Select a photo file
3. Optionally add custom labels (comma-separated)
4. Click Upload
5. Wait for indexing (~5 seconds)
6. Search for the photo using labels

## Author

Kathan Gabani (kdg7224)

## Course

CS-GY 9223: Cloud Computing and Big Data Systems - Fall 2024
