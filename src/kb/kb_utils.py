import random
import time
import json


def create_bedrock_execution_role(iam_client, bucket_name, account_number, suffix, region_name):
    foundation_model_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                ],
                "Resource": [
                    f"arn:aws:bedrock:{region_name}::foundation-model/amazon.titan-embed-text-v1",
                    f"arn:aws:bedrock:{region_name}::foundation-model/amazon.titan-embed-text-v2:0",
                    f"arn:aws:bedrock:{region_name}::foundation-model/cohere.embed-english-v3"
                ]
            }
        ]
    }

    s3_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "S3ListBucketStatement",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:ResourceAccount": [
                            f"{account_number}"
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
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:ResourceAccount": [
                            f"{account_number}"
                        ]
                    }
                }
            }
        ]
    }

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    # create policies based on the policy documents
    fm_policy = iam_client.create_policy(
        PolicyName= f'AmazonBedrockFoundationModelPolicyForKnowledgeBase_{suffix}',
        PolicyDocument=json.dumps(foundation_model_policy_document),
        Description='Policy for accessing foundation model',
    )

    s3_policy = iam_client.create_policy(
        PolicyName=f'AmazonBedrockS3PolicyForKnowledgeBase_{suffix}',
        PolicyDocument=json.dumps(s3_policy_document),
        Description='Policy for reading documents from s3')

    # create bedrock execution role
    bedrock_kb_execution_role = iam_client.create_role(
        RoleName=f'AmazonBedrockExecutionRoleForKnowledgeBase_{suffix}',
        AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
        Description='Amazon Bedrock Knowledge Base Execution Role for accessing OSS and S3',
        MaxSessionDuration=3600
    )

    # fetch arn of the policies and role created above
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']
    s3_policy_arn = s3_policy["Policy"]["Arn"]
    fm_policy_arn = fm_policy["Policy"]["Arn"]
    

    # attach policies to Amazon Bedrock execution role
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=fm_policy_arn
    )
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=s3_policy_arn
    )
    return bedrock_kb_execution_role


def create_oss_policy_attach_bedrock_execution_role(iam_client, collection_id, bedrock_kb_execution_role, suffix, account_number, region_name):
    # define oss policy document
    oss_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll"
                ],
                "Resource": [
                    f"arn:aws:aoss:{region_name}:{account_number}:collection/{collection_id}"
                ]
            }
        ]
    }
    oss_policy = iam_client.create_policy(
        PolicyName=f'AmazonBedrockOSSPolicyForKnowledgeBase_{suffix}',
        PolicyDocument=json.dumps(oss_policy_document),
        Description='Policy for accessing opensearch serverless',
    )
    oss_policy_arn = oss_policy["Policy"]["Arn"]
    print("Opensearch serverless arn: ", oss_policy_arn)

    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=oss_policy_arn
    )
    return None


def create_policies_in_oss(vector_store_name, aoss_client, bedrock_kb_execution_role_arn, suffix, identity):
    encryption_policy = aoss_client.create_security_policy(
        name=f"bedrock-sample-rag-sp-{suffix}",
        policy=json.dumps(
            {
                'Rules': [{'Resource': ['collection/' + vector_store_name],
                           'ResourceType': 'collection'}],
                'AWSOwnedKey': True
            }),
        type='encryption'
    )

    network_policy = aoss_client.create_security_policy(
        name=f"bedrock-sample-rag-np-{suffix}",
        policy=json.dumps(
            [
                {'Rules': [{'Resource': ['collection/' + vector_store_name],
                            'ResourceType': 'collection'}],
                 'AllowFromPublic': True}
            ]),
        type='network'
    )
    access_policy = aoss_client.create_access_policy(
        name=f'bedrock-sample-rag-ap-{suffix}',
        policy=json.dumps(
            [
                {
                    'Rules': [
                        {
                            'Resource': ['collection/' + vector_store_name],
                            'Permission': [
                                'aoss:CreateCollectionItems',
                                'aoss:DeleteCollectionItems',
                                'aoss:UpdateCollectionItems',
                                'aoss:DescribeCollectionItems'],
                            'ResourceType': 'collection'
                        },
                        {
                            'Resource': ['index/' + vector_store_name + '/*'],
                            'Permission': [
                                'aoss:CreateIndex',
                                'aoss:DeleteIndex',
                                'aoss:UpdateIndex',
                                'aoss:DescribeIndex',
                                'aoss:ReadDocument',
                                'aoss:WriteDocument'],
                            'ResourceType': 'index'
                        }],
                    'Principal': [identity, bedrock_kb_execution_role_arn],
                    'Description': 'Easy data policy'}
            ]),
        type='data'
    )
    return encryption_policy, network_policy, access_policy


# AWS Bedrock Knowledge Base
def create_bedrock_knowledge_base(name, index_name, client, role_arn, collection_arn):
    response = client.create_knowledge_base(
        name=name,
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "dimensions": 1024,
                        "embeddingDataType": "FLOAT32"
                    }
                }
            }
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": collection_arn,
                "vectorIndexName": f"{index_name}",
                "fieldMapping": {
                    "vectorField": "vector",
                    "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                    "metadataField": "AMAZON_BEDROCK_METADATA"
                }
            }
        }
    )
    return response["knowledgeBase"]["knowledgeBaseArn"]

def create_data_source_and_sync(client, kb_id, bucket_name):
    response = client.create_data_source(
        name="my-data-source",
        knowledgeBaseId=kb_id,
        dataSourceConfiguration={
            'type': 'S3',
            's3Configuration': {
                'bucketArn': f'arn:aws:s3:::{bucket_name}'
            }
        },
        vectorIngestionConfiguration={
            'chunkingConfiguration': {
                'chunkingStrategy': 'FIXED_SIZE',
                'fixedSizeChunkingConfiguration': {
                    'maxTokens': 500,
                    'overlapPercentage': 10
                }
            }
        },
        description='My data source for knowledge base'
        )

    data_source_id = response['dataSource']['dataSourceId']
    print(f"Data source created: {data_source_id}")

    # Step 2: Sync the Data Source
    sync_response = client.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=data_source_id
    )

    ingestion_job_id = sync_response['ingestionJob']['ingestionJobId']
    print("Ingestion job started:", ingestion_job_id)

    # Poll for the ingestion job status
    while True:
        response = client.get_ingestion_job(
            knowledgeBaseId=kb_id,
            ingestionJobId=ingestion_job_id,
            dataSourceId=data_source_id
        )
        status = response['ingestionJob']['status']
        print(f"Ingestion job status: {status}")

        if status in ['COMPLETE', 'FAILED']:
            break

        # Wait for a few seconds before polling again
        time.sleep(10)

    if status == 'COMPLETE':
        print("Ingestion job completed successfully.")
    elif status == 'FAILED':
        print("Ingestion job failed.")
        print("Error message:", response['ingestionJob'].get('errorMessage', 'No error message provided.'))

def interactive_sleep(seconds: int):
    dots = ''
    for i in range(seconds):
        dots += '.'
        print(dots, end='\r')
        time.sleep(1)

