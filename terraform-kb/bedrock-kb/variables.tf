variable "s3_bucket_name" {
  type        = string
  description = "Name of the S3 bucket for the KB documents"
}

variable "collection_arn" {
  type        = string
  description = "ARN of OpenSearch Serverless collection"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}