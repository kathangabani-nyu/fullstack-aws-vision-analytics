# PowerShell script to create IAM role for OpenSearch master user

$accountId = (aws sts get-caller-identity --query Account --output text)
$region = "us-east-1"
$roleName = "opensearch-master-role"

Write-Host "Creating IAM role for OpenSearch master user..."
Write-Host "Account ID: $accountId"
Write-Host "Role Name: $roleName"

# Create trust policy
$trustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                AWS = "arn:aws:iam::${accountId}:root"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 10

$trustPolicy | Out-File -FilePath opensearch-trust-policy.json -Encoding utf8

# Create the role
Write-Host "Creating IAM role..."
aws iam create-role `
    --role-name $roleName `
    --assume-role-policy-document file://opensearch-trust-policy.json `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Role created successfully"
} else {
    Write-Host "Role may already exist, continuing..."
}

# Create and attach policy
$policy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @("es:*")
            Resource = "arn:aws:es:${region}:${accountId}:domain/*"
        }
    )
} | ConvertTo-Json -Depth 10

$policy | Out-File -FilePath opensearch-policy.json -Encoding utf8

Write-Host "Attaching policy to role..."
aws iam put-role-policy `
    --role-name $roleName `
    --policy-name OpenSearchAccessPolicy `
    --policy-document file://opensearch-policy.json `
    --region $region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Policy attached successfully"
}

$roleArn = "arn:aws:iam::${accountId}:role/${roleName}"

Write-Host ""
Write-Host "=" * 60
Write-Host "✓ IAM role created successfully!"
Write-Host "=" * 60
Write-Host "Role ARN: $roleArn"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Go to OpenSearch Console → photos domain → Security tab"
Write-Host "2. Click Edit on Fine-grained access control"
Write-Host "3. Under 'Master user', select 'Set IAM ARN as master user'"
Write-Host "4. Enter this ARN: $roleArn"
Write-Host "5. Click Save changes"
Write-Host "6. Wait 2-3 minutes for changes to propagate"
Write-Host "=" * 60

