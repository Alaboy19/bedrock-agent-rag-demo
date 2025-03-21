import boto3
import json

iam_client = boto3.client('iam')
s3_client = boto3.client('s3')
opensearch_client = boto3.client('opensearchserverless')
bedrock_agent_client = boto3.client('bedrock-agent')

# AM Role for Bedrock Knowledge Base
def create_iam_role():
    role_name = "BedrockKBServiceRole"
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }

    response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Sid": "BedrockInvokeModelStatement",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-multilingual-v3"
            ]
            },
            {
            "Sid": "OpenSearchServerlessAPIAccessAllStatement",
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": [
                "arn:aws:aoss:us-east-1:971422704596:collection/1r9mh7gxva7mt4ryu3jc"
            ]
            },
            {
            "Sid": "S3ListBucketStatement",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::rag-bedrock-pdfs-iter1"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:ResourceAccount": [
                        "971422704596"
                    ]
                }
                }
            },
            {
                "Sid": "S3GetObjectStatement",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject"
                ],
                "Resource": [
                    "arn:aws:s3:::rag-bedrock-pdfs-iter1/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:ResourceAccount": [
                            "971422704596"
                        ]
                    }
                }
            }
        ]
    }

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName="BedrockKBPolicy",
        PolicyDocument=json.dumps(policy_document)
    )

    return response["Role"]["Arn"]

# OpenSearch Serverless Collection
def create_opensearch_collection():
    response = opensearch_client.create_collection(
        name="bedrock-kb-collection",
        type="VECTORSEARCH",
        description="Vector store for Bedrock KB",
        encryptionPolicy={
        "type": "AES256"  # Specify the encryption type (e.g., AES256 or AWS_KMS)
    }
    )
    return response["collectionDetail"]["arn"]

# Knowledge Base
def create_bedrock_knowledge_base(role_arn, collection_arn):
    response = bedrock_agent_client.create_knowledge_base(
        name="rag-bedrock-kb",
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": "arn:aws:bedrock:us-west-2::foundation-model/cohere.embed-multilingual-v3:on-demand",
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "dimensions": 1024,
                        "embeddingDataType": "FLOAT32"
                    }
                },
                "supplementalDataStorageConfiguration": {
                    "storageLocation": {
                        "type": "S3",
                        "s3Location": {"uri": "s3://rag-bedrock-pdfs-iter1"}
                    }
                },
                "chunkingConfiguration": {
                    "chunkingStrategy": "SEMANTIC",
                    "semanticChunkingConfiguration": {
                        "maxBufferSize": 0,
                        "maxTokens": 300,
                        "sentenceSimilarityThreshold": 95
                    }
                }
            }
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": collection_arn,
                "vectorIndexName": "bedrock-kb-index",
                "fieldMapping": {
                    "vectorField": "bedrock-kb-vector",
                    "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                    "metadataField": "AMAZON_BEDROCK_METADATA"
                }
            }
        }
    )
    return response["knowledgeBase"]["knowledgeBaseArn"]


if __name__ == "__main__":
    print("Creating IAM Role...")
    role_arn = create_iam_role()
    print(f"IAM Role ARN: {role_arn}")

    print("Creating OpenSearch Serverless Collection...")
    collection_arn = create_opensearch_collection()
    print(f"OpenSearch Collection ARN: {collection_arn}")

    print("Creating AWS Bedrock Knowledge Base...")
    kb_arn = create_bedrock_knowledge_base(role_arn, collection_arn)
    print(f"Knowledge Base ARN: {kb_arn}")

    print("✅ AWS Bedrock Knowledge Base setup is complete!")