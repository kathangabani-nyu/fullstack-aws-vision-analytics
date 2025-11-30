# Finding and Using the OpenSearch Master User Role

Since fine-grained access control is enabled, you need to use the IAM role that was set as the master user to create the index.

## Step 1: Find the Master User IAM Role

### Option A: Check OpenSearch Console

1. Go to: https://console.aws.amazon.com/es/
2. Click on domain: `photos`
3. Go to **Security** tab
4. Scroll to **Fine-grained access control** section
5. Look for **Master user** - it should show an IAM ARN like:
   ```
   arn:aws:iam::837134650320:role/ROLE_NAME
   ```
6. Copy that ARN

### Option B: Check CloudFormation/Manual Creation

If you created OpenSearch via CloudFormation or manually, check:
- What IAM role ARN you entered when creating the domain
- Or check your notes/documentation

## Step 2: Use the Master Role to Create Index

Once you have the IAM role ARN, run:

```bash
python backend/scripts/create-index-with-master-role.py
```

When prompted, enter the IAM role ARN.

## Alternative: Temporarily Disable Fine-Grained Access Control

If you can't find the master user role, you can temporarily:

1. **Disable fine-grained access control:**
   - Go to OpenSearch Console → `photos` domain → Security tab
   - Click **Edit** on Fine-grained access control
   - Uncheck **Enable fine-grained access control**
   - Click **Save changes**
   - Wait for the update to complete (~5-10 minutes)

2. **Create the index:**
   ```bash
   python backend/scripts/setup-opensearch-index.py
   ```

3. **Re-enable fine-grained access control:**
   - Go back to Security tab
   - Re-enable fine-grained access control
   - Set the master user (same IAM role as before)
   - Click **Save changes**

**Note:** This approach works but requires waiting for domain updates twice.

## Recommended: Find the Master User Role

The best approach is to find the master user IAM role ARN and use it. Once you have it, share it with me and I can help create the index.

