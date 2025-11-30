#!/usr/bin/env python3
"""
Create CodePipeline for frontend and backend deployments.
"""

import boto3
import json
import time

REGION = 'us-east-1'
GITHUB_REPO = 'kathangabani-nyu/fullstack-aws-vision-analytics'
GITHUB_BRANCH = 'main'

def create_codepipeline_role():
    """Create IAM role for CodePipeline."""
    iam = boto3.client('iam', region_name=REGION)
    
    role_name = 'CodePipelineRole'
    
    try:
        role = iam.get_role(RoleName=role_name)
        print(f"Using existing role: {role['Role']['Arn']}")
        return role['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        pass
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "codepipeline.amazonaws.com",
                        "codebuild.amazonaws.com"
                    ]
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role for CodePipeline and CodeBuild'
    )
    
    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/AWSCodePipeline_FullAccess',
        'arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess',
        'arn:aws:iam::aws:policy/AmazonS3FullAccess',
        'arn:aws:iam::aws:policy/AWSLambda_FullAccess',
        'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess',
    ]
    
    for policy_arn in policies:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    
    print(f"Created role: {role['Role']['Arn']}")
    time.sleep(10)  # Wait for propagation
    return role['Role']['Arn']


def create_artifact_bucket():
    """Create S3 bucket for pipeline artifacts."""
    s3 = boto3.client('s3', region_name=REGION)
    
    bucket_name = 'photo-album-codepipeline-artifacts'
    
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Using existing bucket: {bucket_name}")
        return bucket_name
    except:
        pass
    
    s3.create_bucket(Bucket=bucket_name)
    print(f"Created bucket: {bucket_name}")
    return bucket_name


def create_codebuild_projects(role_arn):
    """Create CodeBuild projects for frontend and backend."""
    codebuild = boto3.client('codebuild', region_name=REGION)
    
    projects = []
    
    # Frontend build project
    frontend_project = {
        'name': 'photo-album-frontend-build',
        'source': {
            'type': 'CODEPIPELINE',
            'buildspec': '''
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 18
  build:
    commands:
      - echo "Building frontend..."
      - cd frontend
      - ls -la
  post_build:
    commands:
      - echo "Deploying to S3..."
      - aws s3 sync . s3://photo-album-stack-frontend-bucket/ --delete --exclude "buildspec.yml"
artifacts:
  files:
    - '**/*'
  base-directory: frontend
'''
        },
        'artifacts': {
            'type': 'CODEPIPELINE'
        },
        'environment': {
            'type': 'LINUX_CONTAINER',
            'image': 'aws/codebuild/amazonlinux2-x86_64-standard:5.0',
            'computeType': 'BUILD_GENERAL1_SMALL'
        },
        'serviceRole': role_arn
    }
    
    # Backend build project
    backend_project = {
        'name': 'photo-album-backend-build',
        'source': {
            'type': 'CODEPIPELINE',
            'buildspec': '''
version: 0.2
phases:
  install:
    runtime-versions:
      python: 3.9
  build:
    commands:
      - echo "Building Lambda functions..."
      - cd backend/lambda/index-photos
      - zip -r ../../../index-photos.zip lambda_function.py
      - cd ../search-photos
      - zip -r ../../../search-photos.zip lambda_function.py
      - cd ../../..
  post_build:
    commands:
      - echo "Deploying Lambda functions..."
      - aws lambda update-function-code --function-name index-photos --zip-file fileb://index-photos.zip
      - aws lambda update-function-code --function-name search-photos --zip-file fileb://search-photos.zip
artifacts:
  files:
    - index-photos.zip
    - search-photos.zip
'''
        },
        'artifacts': {
            'type': 'CODEPIPELINE'
        },
        'environment': {
            'type': 'LINUX_CONTAINER',
            'image': 'aws/codebuild/amazonlinux2-x86_64-standard:5.0',
            'computeType': 'BUILD_GENERAL1_SMALL'
        },
        'serviceRole': role_arn
    }
    
    for project in [frontend_project, backend_project]:
        try:
            codebuild.delete_project(name=project['name'])
            time.sleep(2)
        except:
            pass
        
        codebuild.create_project(**project)
        print(f"Created CodeBuild project: {project['name']}")
        projects.append(project['name'])
    
    return projects


def create_github_connection():
    """Create CodeStar connection for GitHub (requires manual approval in console)."""
    codestar = boto3.client('codestar-connections', region_name=REGION)
    
    connection_name = 'github-connection'
    
    # Check existing connections
    connections = codestar.list_connections()
    for conn in connections.get('Connections', []):
        if conn['ConnectionName'] == connection_name:
            if conn['ConnectionStatus'] == 'AVAILABLE':
                print(f"Using existing connection: {conn['ConnectionArn']}")
                return conn['ConnectionArn']
            else:
                print(f"Connection exists but needs approval: {conn['ConnectionArn']}")
                print("Please go to AWS Console > Developer Tools > Connections and approve it")
                return conn['ConnectionArn']
    
    # Create new connection
    response = codestar.create_connection(
        ConnectionName=connection_name,
        ProviderType='GitHub'
    )
    
    print(f"Created connection: {response['ConnectionArn']}")
    print("IMPORTANT: You need to manually approve this connection in AWS Console!")
    print("Go to: Developer Tools > Settings > Connections")
    
    return response['ConnectionArn']


def create_pipelines(role_arn, artifact_bucket, connection_arn):
    """Create CodePipeline for frontend and backend."""
    codepipeline = boto3.client('codepipeline', region_name=REGION)
    
    # Frontend pipeline
    frontend_pipeline = {
        'name': 'photo-album-frontend-pipeline',
        'roleArn': role_arn,
        'artifactStore': {
            'type': 'S3',
            'location': artifact_bucket
        },
        'stages': [
            {
                'name': 'Source',
                'actions': [
                    {
                        'name': 'SourceAction',
                        'actionTypeId': {
                            'category': 'Source',
                            'owner': 'AWS',
                            'provider': 'CodeStarSourceConnection',
                            'version': '1'
                        },
                        'configuration': {
                            'ConnectionArn': connection_arn,
                            'FullRepositoryId': GITHUB_REPO,
                            'BranchName': GITHUB_BRANCH,
                            'OutputArtifactFormat': 'CODE_ZIP'
                        },
                        'outputArtifacts': [{'name': 'SourceOutput'}]
                    }
                ]
            },
            {
                'name': 'Build',
                'actions': [
                    {
                        'name': 'BuildAction',
                        'actionTypeId': {
                            'category': 'Build',
                            'owner': 'AWS',
                            'provider': 'CodeBuild',
                            'version': '1'
                        },
                        'configuration': {
                            'ProjectName': 'photo-album-frontend-build'
                        },
                        'inputArtifacts': [{'name': 'SourceOutput'}],
                        'outputArtifacts': [{'name': 'BuildOutput'}]
                    }
                ]
            }
        ]
    }
    
    # Backend pipeline
    backend_pipeline = {
        'name': 'photo-album-backend-pipeline',
        'roleArn': role_arn,
        'artifactStore': {
            'type': 'S3',
            'location': artifact_bucket
        },
        'stages': [
            {
                'name': 'Source',
                'actions': [
                    {
                        'name': 'SourceAction',
                        'actionTypeId': {
                            'category': 'Source',
                            'owner': 'AWS',
                            'provider': 'CodeStarSourceConnection',
                            'version': '1'
                        },
                        'configuration': {
                            'ConnectionArn': connection_arn,
                            'FullRepositoryId': GITHUB_REPO,
                            'BranchName': GITHUB_BRANCH,
                            'OutputArtifactFormat': 'CODE_ZIP'
                        },
                        'outputArtifacts': [{'name': 'SourceOutput'}]
                    }
                ]
            },
            {
                'name': 'Build',
                'actions': [
                    {
                        'name': 'BuildAction',
                        'actionTypeId': {
                            'category': 'Build',
                            'owner': 'AWS',
                            'provider': 'CodeBuild',
                            'version': '1'
                        },
                        'configuration': {
                            'ProjectName': 'photo-album-backend-build'
                        },
                        'inputArtifacts': [{'name': 'SourceOutput'}],
                        'outputArtifacts': [{'name': 'BuildOutput'}]
                    }
                ]
            }
        ]
    }
    
    for pipeline in [frontend_pipeline, backend_pipeline]:
        try:
            codepipeline.delete_pipeline(name=pipeline['name'])
            time.sleep(2)
        except:
            pass
        
        codepipeline.create_pipeline(pipeline=pipeline)
        print(f"Created pipeline: {pipeline['name']}")


def main():
    print("="*50)
    print("Creating CodePipeline Infrastructure")
    print("="*50)
    
    # Create IAM role
    print("\n1. Creating IAM role...")
    role_arn = create_codepipeline_role()
    
    # Create artifact bucket
    print("\n2. Creating artifact bucket...")
    artifact_bucket = create_artifact_bucket()
    
    # Create CodeBuild projects
    print("\n3. Creating CodeBuild projects...")
    create_codebuild_projects(role_arn)
    
    # Create GitHub connection
    print("\n4. Creating GitHub connection...")
    connection_arn = create_github_connection()
    
    # Create pipelines
    print("\n5. Creating pipelines...")
    create_pipelines(role_arn, artifact_bucket, connection_arn)
    
    print("\n" + "="*50)
    print("CodePipeline Setup Complete!")
    print("="*50)
    print("\nNOTE: You need to manually approve the GitHub connection")
    print("Go to AWS Console > Developer Tools > Connections")
    print("="*50)


if __name__ == "__main__":
    main()

