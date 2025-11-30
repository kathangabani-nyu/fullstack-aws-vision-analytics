# Creating OpenSearch Index - Final Steps

Since you have fine-grained access control enabled, you need to create the index using one of these methods:

## Method 1: OpenSearch Dashboards (Easiest)

1. **Go to OpenSearch Dashboards:**
   ```
   https://search-photos-web2h5x2a5uhgbveutnorjcgzq.aos.us-east-1.on.aws/_dashboards
   ```

2. **Sign in:**
   - Since you have IAM as master user type, you'll need to sign in with AWS credentials
   - The sign-in process may redirect you to AWS to authenticate
   - Or you may need to use the IAM role ARN that was set as master user

3. **Create the index:**
   - Once signed in, go to **Dev Tools** (left sidebar)
   - Paste this command:
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
   - Click the play button (▶) to execute
   - You should see: `"acknowledged": true`

## Method 2: Configure Role Mapping (If Dashboards Doesn't Work)

If you can't access Dashboards, you may need to configure role mappings. This requires knowing which IAM role was set as the master user.

1. **Find the master user IAM role:**
   - Go to OpenSearch Console → `photos` domain → Security tab
   - Under "Fine-grained access control", check "Master user"
   - Note the IAM ARN (e.g., `arn:aws:iam::837134650320:role/ROLE_NAME`)

2. **Use that role to create the index:**
   ```bash
   # Assume the role
   aws sts assume-role \
     --role-arn "arn:aws:iam::837134650320:role/YOUR_MASTER_ROLE" \
     --role-session-name "opensearch-setup"
   
   # Export the credentials
   # Then run the Python script with those credentials
   ```

## Method 3: Temporarily Disable Fine-Grained Access (Not Recommended)

If the above methods don't work, you could temporarily:
1. Disable fine-grained access control
2. Create the index
3. Re-enable fine-grained access control

**However, this is not recommended** as it may cause issues with your Lambda functions that expect fine-grained access.

## What to Do Next

1. **Try Method 1 first** (OpenSearch Dashboards) - this is the easiest
2. If Dashboards authentication still fails, check:
   - Which IAM role ARN you used as master user
   - Whether that role has the necessary permissions
3. Once the index is created, proceed to update Lambda environment variables

## After Index is Created

Once you've successfully created the index, update your Lambda functions:

```bash
OPENSEARCH_ENDPOINT="search-photos-web2h5x2a5uhgbveutnorjcgzq.us-east-1.es.amazonaws.com"

aws lambda update-function-configuration \
  --function-name index-photos \
  --environment Variables="{OPENSEARCH_ENDPOINT=${OPENSEARCH_ENDPOINT},OPENSEARCH_INDEX=photos,AWS_REGION=us-east-1}" \
  --region us-east-1

aws lambda update-function-configuration \
  --function-name search-photos \
  --environment Variables="{OPENSEARCH_ENDPOINT=${OPENSEARCH_ENDPOINT},OPENSEARCH_INDEX=photos,AWS_REGION=us-east-1}" \
  --region us-east-1
```

## Troubleshooting

**If Dashboards authentication fails:**
- Make sure you're using the IAM role that was set as master user
- Check that the access policy allows your account
- Try signing in with AWS SSO if configured

**If you get permission errors:**
- The master user role needs `indices:admin/create` permission
- This is configured in fine-grained access control role mappings
- You may need to configure this in OpenSearch Dashboards under Security → Roles

