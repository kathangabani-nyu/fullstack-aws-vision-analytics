#!/usr/bin/env python3
"""
Upload sample images to S3 with custom labels.
"""

import boto3
import os

BUCKET = 'photo-album-stack-photos-bucket'
REGION = 'us-east-1'

# Images and their custom labels
IMAGES = [
    ('cat1.jpg', 'cat,pet,feline'),
    ('cat2.jpg', 'cat,pet,orange cat'),
    ('cat3.jpg', 'cat,pet,kitten'),
    ('dog1.jpg', 'dog,pet,labrador'),
    ('dog2.jpg', 'dog,pet,canine'),
    ('dog3.jpg', 'dog,pet,puppy'),
    ('raccoon1.jpg', 'raccoon,wildlife,animal'),
    ('raccoon2.jpg', 'raccoon,wildlife,animal'),
]

def upload_images():
    """Upload images with custom labels."""
    
    s3 = boto3.client('s3', region_name=REGION)
    
    print(f"Uploading images to {BUCKET}...")
    
    for filename, labels in IMAGES:
        filepath = os.path.join(os.getcwd(), filename)
        
        if not os.path.exists(filepath):
            print(f"  Skipping {filename} (not found)")
            continue
        
        try:
            with open(filepath, 'rb') as f:
                s3.put_object(
                    Bucket=BUCKET,
                    Key=filename,
                    Body=f,
                    ContentType='image/jpeg',
                    Metadata={
                        'customlabels': labels
                    }
                )
            print(f"  Uploaded {filename} with labels: {labels}")
        except Exception as e:
            print(f"  Error uploading {filename}: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    upload_images()

