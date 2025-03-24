import os
import boto3
import json
import time 
import pprint
import random
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, RequestError
from kb_utils import (
    interactive_sleep, create_bedrock_knowledge_base, create_data_source_and_sync
)


def create_index(index_name, kb_host, awsauth):
    # Build the OpenSearch client
    oss_client = OpenSearch(
        hosts=[{'host': kb_host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )

    with open("src/kb/body.json", "r") as json_file:
        body_json = json.load(json_file)
        print("body_json: ", body_json)
    try:
        response = oss_client.indices.create(index=index_name, body=body_json)
        print('\nCreating index:')
        pp.pprint(response)

        # index creation can take up to a minute
        interactive_sleep(60)
    except RequestError as e:
        # you can delete the index if its already exists
        # oss_client.indices.delete(index=index_name)
        print(f'Error while trying to create the index, with error {e.error}\nyou may unmark the delete above to delete, and recreate the index')



if __name__ == "__main__":
    
    load_dotenv()
    suffix = os.getenv("SUFFIX")
    REGION = os.getenv("REGION")
    S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")
    VECTOR_STORE_NAME=os.getenv("COLLECTION_NAME") + f"-{suffix}"
    index_name = f"{VECTOR_STORE_NAME}-index"
 
    #Create index in OpenSearch
    sts_client = boto3.client('sts')
    boto3_session = boto3.session.Session()
    iam_client = boto3_session.client('iam')
    identity = boto3.client('sts').get_caller_identity()['Arn']
    account_id = sts_client.get_caller_identity()["Account"]
    account_number = boto3.client('sts').get_caller_identity().get('Account')
    aoss_client = boto3_session.client('opensearchserverless')
    credentials = boto3.Session().get_credentials()
    pp = pprint.PrettyPrinter(indent=2)
    awsauth = AWSV4SignerAuth(credentials, REGION, 'aoss')
    
    kb_host = os.getenv("KB_HOST")
    
    print("Creating index in OpenSearch for index name", index_name, kb_host, awsauth)
    interactive_sleep(20)
    create_index(index_name, kb_host, awsauth)
    
    #Create the AWS Bedrock Knowledge Base
    client = boto3.client('bedrock-agent',  region_name=REGION)
    print("Creating AWS Bedrock Knowledge Base...")
    kb_name = os.getenv("KNOWLEDGE_BASE_NAME") 
    kb_role_arn = os.getenv("BEDROCK_KB_EXECUTION_ROLE_ARN")
    collection_arn = os.getenv("COLLECTION_ARN")
    kb_arn = create_bedrock_knowledge_base(client=client, 
                                           name=kb_name, 
                                           index_name=index_name, 
                                           collection_arn=collection_arn, 
                                           role_arn=kb_role_arn)
    print(f"Knowledge Base ARN: {kb_arn}")
    interactive_sleep(20)
    kb_id = kb_arn.split('/')[-1]

    #Create data source and sync
    create_data_source_and_sync(client=client, kb_id=kb_id, bucket_name=S3_BUCKET_NAME)
    
    



 
