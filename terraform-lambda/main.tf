provider "aws" {
  region = "us-east-1"
}

# Archive the Lambda function code dynamically
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "../src/lambda_function.py"  # Your Lambda function script
  output_path = "lambda.zip"
}

# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy_attachment" "lambda_basic_execution" {
  name       = "lambda_basic_execution"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Create Lambda function
resource "aws_lambda_function" "my_lambda" {
  function_name    = "lambda_function"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler" 
  runtime        = "python3.8"
  
  memory_size = 128
  timeout     = 10
}

# Add permission for Bedrock to invoke the Lambda function
resource "aws_lambda_permission" "allow_bedrock_invoke" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.my_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:us-east-1:971422704596:agent/*"
}

# Output the Lambda ARN
output "lambda_arn" {
  value = aws_lambda_function.my_lambda.arn
}