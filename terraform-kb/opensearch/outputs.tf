output "collection_arn" {
  value       = aws_opensearchserverless_collection.bedrock_vector_store.arn
  description = "The ARN of the OpenSearch Serverless Collection"
}