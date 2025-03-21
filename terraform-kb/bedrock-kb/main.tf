terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.92.0"  # Replace with the latest version
    }
  }
}
provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "bedrock_kb_role" {
  name = "AmazonBedrockKnowledgeBaseRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "bedrock.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "bedrock_kb_policy" {
  name        = "AmazonBedrockKnowledgeBasePolicy"
  description = "Permissions for Amazon Bedrock Knowledge Base"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "BedrockInvokeModelStatement",
        Effect = "Allow",
        Action = ["bedrock:InvokeModel"],
        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-english-v3"
        ]
      },
      {
        Sid    = "OpenSearchServerlessAPIAccessAllStatement",
        Effect = "Allow",
        Action = ["aoss:APIAccessAll"],
        Resource = [ var.collection_arn ]
      },
      {
        Sid    = "S3ListBucketStatement",
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}"
        ],
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = ["971422704596"]
          }
        }
      },
      {
        Sid    = "S3GetObjectStatement",
        Effect = "Allow",
        Action = ["s3:GetObject"],
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ],
        Condition = {
          StringEquals = {
            "aws:ResourceAccount" = ["971422704596"]
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_kb_policy" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_policy.arn
}

resource "aws_bedrockagent_knowledge_base" "example" {
  name     = "example-knowledge-base"
  role_arn = aws_iam_role.bedrock_kb_role.arn

  knowledge_base_configuration {
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-english-v3"

      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          dimensions          = 1024
          embedding_data_type = "FLOAT32"
        }
      }

      supplemental_data_storage_configuration {
        storage_location {
          type = "S3"

          s3_location {
            uri = "s3://${var.s3_bucket_name}/"
          }
        }
      }
    }
    type = "VECTOR"
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = var.collection_arn
      vector_index_name = "bedrock-vector-store"
      field_mapping {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }
}

resource "aws_bedrock_data_source_sync_job" "sync_job" {
  knowledge_base_id = aws_bedrock_knowledge_base.kb.id
  depends_on        = [aws_bedrock_knowledge_base.kb]
}

output "knowledge_base_id" {
  value       = aws_bedrock_knowledge_base.kb.id
  description = "The ID of the created Knowledge Base"
}