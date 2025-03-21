provider "aws" {
  region = "us-east-1"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

resource "aws_s3_bucket" "knowledge_base_bucket" {
  bucket        = var.s3_bucket_name
  force_destroy = true
}

output "s3_bucket_name" {
  value = aws_s3_bucket.knowledge_base_bucket.id
}