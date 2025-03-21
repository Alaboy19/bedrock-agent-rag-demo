terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.92.0"
    }
  }

  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

data "aws_caller_identity" "current" {}

resource "aws_opensearchserverless_security_policy" "encryption_policy" {
  name        = "bedrock-encryption-policy"
  type        = "encryption"
  description = "Encryption policy for Bedrock vector collection"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection",
        Resource     = ["collection/bedrock-vector-store"]
      }
    ],
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_access_policy" "access_policy" {
  name        = "bedrock-access-policy"
  type        = "data"
  description = "Access policy for Bedrock to interact with collection"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "index",
          Resource     = ["index/bedrock-vector-store/*"],
          Permission   = [
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ],
      Principal = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/AmazonBedrockKnowledgeBaseRole"
      ]
    }
  ])
}

resource "aws_opensearchserverless_security_policy" "network_policy" {
  name        = "bedrock-network-policy"
  type        = "network"
  description = "Allow Bedrock service access to the collection"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource     = ["collection/bedrock-vector-store"]
        }
      ],
      SourceServices  = ["bedrock.amazonaws.com"],
      Description     = "Network policy allowing Bedrock access"
    }
  ])
}

resource "aws_opensearchserverless_collection" "bedrock_vector_store" {
  name = "bedrock-vector-store"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.network_policy,
    aws_opensearchserverless_security_policy.encryption_policy,
    aws_opensearchserverless_access_policy.access_policy
  ]
}