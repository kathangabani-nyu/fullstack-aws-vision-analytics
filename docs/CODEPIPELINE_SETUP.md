# AWS CodePipeline Setup Guide

This guide provides instructions for setting up CodePipeline for automated deployment.

## Prerequisites

1. GitHub repository: https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics
2. CodeBuild service role with appropriate permissions
3. S3 bucket for CodePipeline artifacts (created automatically)

## Backend Pipeline (P1) - Lambda Functions

### Step 1: Create CodeBuild Project

1. Go to CodeBuild Console: https://console.aws.amazon.com/codesuite/codebuild/
2. Click "Create build project"
3. Configure:

**Project Configuration**
- **Project name**: `photo-album-backend-build`
- **Description**: Build and package Lambda functions

**Source**
- **Source provider**: GitHub
- **Repository**: Connect using OAuth or use repository URL
- **Repository URL**: `https://github.com/kathangabani-nyu/fullstack-aws-vision-analytics`
- **Branch**: `main` (or your default branch)
- **Source version**: Latest

**Environment**
- **Environment image**: Managed image
- **Operating system**: Ubuntu
- **Runtime(s)**: Standard
- **Image**: `aws/codebuild/standard:5.0`
- **Image version**: Always use the latest
- **Environment type**: Linux
- **Compute**: 3 GB memory, 2 vCPUs
- **Privileged**: No
- **Service role**: Create new service role (or use existing)

**Buildspec**
- **Buildspec name**: `backend/buildspec.yml`
- **Use a buildspec file**: Yes

**Artifacts**
- **Type**: Amazon S3
- **Bucket name**: Create new or use existing
- **Name**: `photo-album-artifacts` (or your choice)
- **Artifact packaging**: Zip

4. Click "Create build project"

### Step 2: Create Pipeline

1. Go to CodePipeline Console: https://console.aws.amazon.com/codesuite/codepipeline/
2. Click "Create pipeline"
3. Configure:

**Pipeline Settings**
- **Pipeline name**: `photo-album-backend-pipeline`
- **Service role**: Create new (or use existing)
- **Artifact store**: Default location (or custom S3 bucket)

**Source Stage**
- **Source provider**: GitHub (Version 2)
- **Connection**: Create new connection (if first time)
  - Authorize GitHub
  - Select repository: `kathangabani-nyu/fullstack-aws-vision-analytics`
  - Branch: `main`
- **Output artifact format**: CodePipeline default

**Build Stage**
- **Build provider**: AWS CodeBuild
- **Project name**: `photo-album-backend-build` (created above)
- **Build type**: Single build
- **Output artifacts**: `BuildArtifact`

**Deploy Stage**
- **Deploy provider**: AWS Lambda
- **Region**: us-east-1
- **Input artifact**: `BuildArtifact`
- **Lambda function name**: `index-photos`
- **Artifact**: `index-photos.zip`

4. Click "Next" → "Create pipeline"

### Step 3: Add Second Lambda Deployment

After creating the pipeline, add another deployment action for `search-photos`:

1. Edit the pipeline
2. In the Deploy stage, click "Add action"
3. Configure:
   - **Action name**: `DeploySearchPhotos`
   - **Deploy provider**: AWS Lambda
   - **Region**: us-east-1
   - **Input artifact**: `BuildArtifact`
   - **Lambda function name**: `search-photos`
   - **Artifact**: `search-photos.zip`

4. Save changes

### Step 4: Update Buildspec for Multiple Artifacts

The `backend/buildspec.yml` should output both ZIP files. Verify it matches:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.9
    commands:
      - echo "Installing dependencies"
  pre_build:
    commands:
      - echo "Preparing Lambda function packages"
  build:
    commands:
      - echo "Building Lambda functions"
      - |
        cd lambda/index-photos
        pip install -r requirements.txt -t .
        zip -r ../../../index-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*"
      - |
        cd lambda/search-photos
        pip install -r requirements.txt -t .
        zip -r ../../../search-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*"
  post_build:
    commands:
      - echo "Build completed successfully"

artifacts:
  files:
    - 'index-photos.zip'
    - 'search-photos.zip'
  base-directory: .
```

## Frontend Pipeline (P2) - S3 Deployment

### Step 1: Create CodeBuild Project

1. Go to CodeBuild Console
2. Click "Create build project"
3. Configure:

**Project Configuration**
- **Project name**: `photo-album-frontend-build`

**Source**
- Same as backend (GitHub repository)

**Environment**
- **Environment image**: Managed image
- **Operating system**: Ubuntu
- **Runtime(s)**: Standard
- **Image**: `aws/codebuild/standard:5.0`

**Buildspec**
- **Buildspec name**: `frontend/buildspec.yml`

**Artifacts**
- **Type**: No artifacts (or S3 if you want to store)

**Environment Variables**
- Add variable:
  - **Name**: `FRONTEND_BUCKET_NAME`
  - **Value**: Your frontend bucket name (e.g., `photo-album-stack-frontend-bucket`)

4. Click "Create build project"

### Step 2: Update IAM Permissions

The CodeBuild service role needs S3 permissions:

1. Go to IAM Console
2. Find the CodeBuild service role
3. Attach policy or add inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_FRONTEND_BUCKET_NAME/*",
        "arn:aws:s3:::YOUR_FRONTEND_BUCKET_NAME"
      ]
    }
  ]
}
```

### Step 3: Create Pipeline

1. Go to CodePipeline Console
2. Click "Create pipeline"
3. Configure:

**Pipeline Settings**
- **Pipeline name**: `photo-album-frontend-pipeline`

**Source Stage**
- Same as backend pipeline

**Build Stage**
- **Build provider**: AWS CodeBuild
- **Project name**: `photo-album-frontend-build`

**Deploy Stage**
- **Deploy provider**: Amazon S3
- **Region**: us-east-1
- **Bucket name**: Your frontend bucket name
- **Extract file before deploy**: No
- **Input artifact**: `BuildArtifact`

4. Click "Next" → "Create pipeline"

## Testing the Pipelines

### Test Backend Pipeline

1. Make a small change to a Lambda function
2. Commit and push to GitHub
3. Pipeline should automatically trigger
4. Monitor pipeline execution
5. Verify Lambda functions are updated

### Test Frontend Pipeline

1. Make a change to frontend files
2. Commit and push to GitHub
3. Pipeline should automatically trigger
4. Monitor pipeline execution
5. Verify files are deployed to S3
6. Check frontend website for changes

## Troubleshooting

### Pipeline not triggering
- Check GitHub webhook is configured
- Verify repository connection
- Check branch name matches

### Build fails
- Check CodeBuild logs
- Verify buildspec.yml syntax
- Check dependencies are available

### Deployment fails
- Verify IAM permissions
- Check Lambda function names
- Verify S3 bucket names

### Artifacts not found
- Check artifact names in buildspec
- Verify artifact paths
- Check CodeBuild logs

## Manual Pipeline Execution

You can manually trigger pipelines:

1. Go to CodePipeline console
2. Select your pipeline
3. Click "Release change"

## Cost Optimization

- CodePipeline: First pipeline is free, additional pipelines cost per month
- CodeBuild: Pay per build minute (first 100 minutes/month free)
- S3 artifacts: Minimal storage costs

## Cleanup

To delete pipelines:

1. Go to CodePipeline console
2. Select pipeline
3. Click "Delete"
4. Also delete CodeBuild projects if not needed

