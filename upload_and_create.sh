#!/bin/bash

set -e  # Exit on error

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

echo "Using S3 bucket name from .env: $S3_BUCKET_NAME"

echo "Creating S3 bucket..."
cd terraform-s3
terraform init
terraform apply -auto-approve -var "s3_bucket_name=$S3_BUCKET_NAME"

echo "S3 bucket created: $S3_BUCKET_NAME"
cd ../

echo "Uploading files to S3..."
python3 src/data_ingestion.py "$S3_BUCKET_NAME"

echo "Files uploaded to S3"

echo "Deploying Lambda function..."
cd terraform-lambda
terraform init
terraform apply -auto-approve

# Export Lambda ARN as an environment variable
export LAMBDA_FUNCTION_ARN=$(terraform output -raw lambda_arn)
echo "Lambda function deployed. ARN exported as environment variable: $LAMBDA_FUNCTION_ARN"