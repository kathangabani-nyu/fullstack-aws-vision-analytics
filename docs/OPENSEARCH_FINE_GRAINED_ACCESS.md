# OpenSearch Fine-Grained Access Control Setup

This guide explains how to configure fine-grained access control for your OpenSearch domain.

## Master User Configuration

When creating the OpenSearch domain with fine-grained access control, you need to specify a master user. You have two options:

### Option 1: Use IAM ARN (Recommended)

Enter the ARN of an IAM role that will have master access to OpenSearch.

#### Using Lambda Role ARN

After deploying the CloudFormation stack, you can use one of the Lambda role ARNs:

**Index Photos Lambda Role:**
```
arn:aws:iam::YOUR_ACCOUNT_ID:role/photo-album-stack-index-photos-role
```

**Search Photos Lambda Role:**
```
arn:aws:iam::YOUR_ACCOUNT_ID:role/photo-album-stack-search-photos-role
```

**To get your Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

**Example:**
If your account ID is `123456789012`, enter:
```
arn:aws:iam::123456789012:role/photo-album-stack-index-photos-role
```

#### Using Dedicated IAM Role (More Secure)

Create a dedicated IAM role specifically for OpenSearch master access:

1. **Create the role using the script:**
   ```bash
   cd backend/scripts
   chmod +x create-opensearch-master-role.sh
   ./create-opensearch-master-role.sh
   ```

2. **Or create manually in IAM Console:**
   - Go to IAM Console → Roles → Create role
   - Trust entity: AWS account (your account)
   - Role name: `opensearch-master-role`
   - Attach policy with OpenSearch permissions:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": ["es:*"],
           "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/*"
         }
       ]
     }
     ```

3. **Use the role ARN:**
   ```
   arn:aws:iam::YOUR_ACCOUNT_ID:role/opensearch-master-role
   ```

### Option 2: Create Master User (Alternative)

Instead of IAM ARN, you can create a master user with username/password:

1. Select "Create master user"
2. Enter:
   - **Username**: `opensearch-master` (or your choice)
   - **Password**: Create a strong password (save it securely)

**Note**: Using IAM ARN is recommended as it's more secure and doesn't require managing passwords.

## Access Policy Configuration

After setting up fine-grained access control, configure the domain access policy:

### Option 1: Allow Lambda Roles Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::YOUR_ACCOUNT_ID:role/photo-album-stack-index-photos-role",
          "arn:aws:iam::YOUR_ACCOUNT_ID:role/photo-album-stack-search-photos-role"
        ]
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/photos/*"
    }
  ]
}
```

### Option 2: Allow All from Your Account (Simpler)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/photos/*"
    }
  ]
}
```

## Lambda Function Authentication

When using fine-grained access control with IAM, your Lambda functions need to use AWS Signature Version 4 (SigV4) for authentication. The code already includes this using `requests-aws4auth`.

The Lambda functions automatically use the execution role credentials to authenticate with OpenSearch.

## Testing Access

After setup, test that Lambda functions can access OpenSearch:

1. Upload a photo via the frontend
2. Check CloudWatch logs for `index-photos` Lambda
3. Look for successful indexing messages
4. If you see authentication errors, verify:
   - IAM role ARN is correct
   - Domain access policy allows the role
   - Lambda execution role has OpenSearch permissions

## Troubleshooting

### "Access Denied" Errors

- Verify the IAM role ARN is correct in OpenSearch master user settings
- Check domain access policy includes the Lambda roles
- Ensure Lambda execution roles have `es:*` permissions

### Authentication Failures

- Verify `requests-aws4auth` is installed in Lambda package
- Check that Lambda execution role credentials are being used
- Review CloudWatch logs for detailed error messages

### Cannot Create Index

- Ensure master user has full permissions
- Check domain access policy allows index creation
- Verify you're using the correct endpoint URL

## Security Best Practices

1. **Use IAM Roles**: Prefer IAM ARN over username/password
2. **Least Privilege**: Grant only necessary permissions
3. **VPC Access**: Consider VPC access for production (more secure)
4. **Encryption**: Enable encryption at rest
5. **HTTPS Only**: Ensure all connections use HTTPS

## Quick Reference

**To find your Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

**To find Lambda role ARN after CloudFormation:**
```bash
aws iam get-role --role-name photo-album-stack-index-photos-role --query 'Role.Arn' --output text
```

**Master User ARN Format:**
```
arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME
```

Replace:
- `ACCOUNT_ID` with your AWS account ID
- `ROLE_NAME` with the IAM role name

