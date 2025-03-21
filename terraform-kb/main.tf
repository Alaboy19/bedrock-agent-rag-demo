provider "aws" {
  region = "us-east-1"
}

# IAM Role for Amazon Bedrock Knowledge Base
resource "aws_iam_role" "bedrock_kb_role" {
  name = "AmazonBedrockKnowledgeBaseRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# IAM Policy for Bedrock Knowledge Base
resource "aws_iam_policy" "bedrock_kb_policy" {
  name        = "AmazonBedrockKnowledgeBasePolicy"
  description = "Permissions for Amazon Bedrock Knowledge Base"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvokeModelStatement"
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-english-v3"
        ]
      },
      {
        Sid    = "OpenSearchServerlessAPIAccessAllStatement"
        Effect = "Allow"
        Action = ["aoss:APIAccessAll"]
        Resource = [
          "arn:aws:aoss:us-east-1:971422704596:collection/wp8q5wckhxsl2ypo1sx1"
        ]
      },
      {
        Sid    = "S3ListBucketStatement"
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::my-knowledge-base-bucket-expats-rag"
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = ["971422704596"]
          }
        }
      },
      {
        Sid    = "S3GetObjectStatement"
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = [
          "arn:aws:s3:::my-knowledge-base-bucket-expats-rag/*"
        ]
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = ["971422704596"]
          }
        }
      }
    ]
  })
}

# Attach IAM Policy to the Role
resource "aws_iam_role_policy_attachment" "attach_kb_policy" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_policy.arn
}

# Amazon Bedrock Knowledge Base
resource "aws_bedrock_knowledge_base" "kb" {
  name                 = "knowledge-base-quick-start-nv84r"
  role_arn             = aws_iam_role.bedrock_kb_role.arn
  knowledge_base_type  = "VECTOR"

  data_source_configuration {
    s3_configuration {
      s3_uri = "s3://rag-bedrock-pdfs-iter1"
    }
  }

  embedding_model_configuration {
    provider = "cohere"
    model    = "embed-english-v3"
    mode     = "ON_DEMAND"
  }

  chunking_configuration {
    strategy = "SEMANTIC"
    semantic_chunking_configuration {
      max_buffer_size       = 0
      max_token_size        = 300
      similarity_threshold  = 95
    }
  }

  vector_store_configuration {
    type         = "OPENSEARCH_SERVERLESS"
    quick_create = true
  }
}

# **Trigger Data Source Sync After Knowledge Base Creation**
resource "aws_bedrock_data_source_sync_job" "sync_job" {
  knowledge_base_id = aws_bedrock_knowledge_base.kb.id
  depends_on        = [aws_bedrock_knowledge_base.kb]
}
