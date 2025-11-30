#!/bin/bash

# Script to package Lambda functions with dependencies

echo "Packaging Lambda functions..."

# Package index-photos Lambda
echo "Packaging index-photos Lambda..."
cd lambda/index-photos
pip install -r requirements.txt -t . --quiet
zip -r ../../../index-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*" "*.zip"
cd ../../..

# Package search-photos Lambda
echo "Packaging search-photos Lambda..."
cd lambda/search-photos
pip install -r requirements.txt -t . --quiet
zip -r ../../../search-photos.zip . -x "*.pyc" "__pycache__/*" "*.git*" "*.zip"
cd ../../..

echo "Packaging complete!"
echo "Files created:"
echo "  - index-photos.zip"
echo "  - search-photos.zip"
echo ""
echo "To update Lambda functions:"
echo "  aws lambda update-function-code --function-name index-photos --zip-file fileb://index-photos.zip"
echo "  aws lambda update-function-code --function-name search-photos --zip-file fileb://search-photos.zip"

