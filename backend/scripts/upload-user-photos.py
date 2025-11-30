#!/usr/bin/env python3
"""
Upload user's photos to S3 with custom labels.
"""

import boto3
import os

BUCKET = 'photo-album-stack-photos-bucket'
REGION = 'us-east-1'
PHOTOS_DIR = r'C:\Users\katha\OneDrive\Desktop\Cloud Computing\assignment 3\photos'

# Images and their custom labels
IMAGES = [
    ('cat11.jpeg', 'cat,pet,feline'),
    ('cat12.jpeg', 'cat,pet,feline'),
    ('cow-humans.jpg', 'cow,human,people,farm,animal'),
    ('goat.jpg', 'goat,farm,animal'),
    ('human-raccoon.jpg', 'human,raccoon,people,wildlife'),
    ('human_raccoon.jpg', 'human,raccoon,people,wildlife'),
    ('llama.jpg', 'llama,animal,farm'),
    ('pig.jpg', 'pig,farm,animal'),
]

def get_content_type(filename):
    if filename.endswith('.jpeg') or filename.endswith('.jpg'):
        return 'image/jpeg'
    elif filename.endswith('.png'):
        return 'image/png'
    return 'application/octet-stream'

def upload_images():
    """Upload images with custom labels."""
    
    s3 = boto3.client('s3', region_name=REGION)
    
    print(f"Uploading photos from {PHOTOS_DIR} to {BUCKET}...")
    
    for filename, labels in IMAGES:
        filepath = os.path.join(PHOTOS_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"  Skipping {filename} (not found)")
            continue
        
        try:
            with open(filepath, 'rb') as f:
                s3.put_object(
                    Bucket=BUCKET,
                    Key=filename,
                    Body=f,
                    ContentType=get_content_type(filename),
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

