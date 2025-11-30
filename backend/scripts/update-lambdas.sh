#!/bin/bash

# Script to update Lambda functions after packaging

FUNCTION_1="index-photos"
FUNCTION_2="search-photos"
REGION="us-east-1"

echo "Updating Lambda functions..."

if [ ! -f "index-photos.zip" ]; then
    echo "Error: index-photos.zip not found. Run package-lambdas.sh first."
    exit 1
fi

if [ ! -f "search-photos.zip" ]; then
    echo "Error: search-photos.zip not found. Run package-lambdas.sh first."
    exit 1
fi

echo "Updating $FUNCTION_1..."
aws lambda update-function-code \
    --function-name $FUNCTION_1 \
    --zip-file fileb://index-photos.zip \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ $FUNCTION_1 updated successfully"
else
    echo "✗ Failed to update $FUNCTION_1"
    exit 1
fi

echo "Updating $FUNCTION_2..."
aws lambda update-function-code \
    --function-name $FUNCTION_2 \
    --zip-file fileb://search-photos.zip \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✓ $FUNCTION_2 updated successfully"
else
    echo "✗ Failed to update $FUNCTION_2"
    exit 1
fi

echo ""
echo "All Lambda functions updated successfully!"

