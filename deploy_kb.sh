#!/bin/bash

set -euo pipefail

echo "🔄 Loading environment variables from .env..."
set -a
source .env
set +a


# Export TF_VARs for Terraform
export TF_VAR_s3_bucket_name=$S3_BUCKET_NAME
export TF_VAR_aws_region=$REGION

cd terraform-kb

# Deploy OpenSearch Serverless Collection

echo "🚀 [Step 1/2] Deploying OpenSearch Serverless Collection..."
cd opensearch
terraform init 
terraform apply -auto-approve

# Capture the ARN output from Terraform
COLLECTION_ARN=$(terraform output -raw collection_arn)
echo "✅ OpenSearch Collection ARN: $COLLECTION_ARN"
export TF_VAR_collection_arn=$COLLECTION_ARN
export TF_VAR_s3_bucket_name=$S3_BUCKET_NAME



#Deploy Bedrock Knowledge Base

echo "🚀 [Step 2/2] Deploying Amazon Bedrock Knowledge Base..."
cd ../bedrock-kb
terraform init 
terraform apply -auto-approve

# Capture and show the Knowledge Base ID
KB_ID=$(terraform output -raw knowledge_base_id)
echo "🎉 Deployment complete!"
echo "📘 Knowledge Base ID: $KB_ID"