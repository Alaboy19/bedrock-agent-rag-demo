import os
import boto3
import json
import time 
import pprint
import random
from dotenv import load_dotenv, set_key
from kb_utils import (
    create_bedrock_execution_role, create_oss_policy_attach_bedrock_execution_role, 
    create_policies_in_oss, interactive_sleep
)
def create_policies(iam_client, bucket_name, account_number, suffix, region_name, vector_store_name, identity):
    
    bedrock_kb_execution_role = create_bedrock_execution_role(iam_client=iam_client,
                                                              bucket_name=bucket_name, 
                                                              suffix=suffix,
                                                              account_number=account_number,
                                                              region_name=region_name
    )
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']
    set_key('.env', "BEDROCK_KB_EXECUTION_ROLE_ARN", bedrock_kb_execution_role_arn)
    aoss_client = boto3_session.client('opensearchserverless')
    # create security, network and data access policies within OSS
    #vector_store_name, aoss_client, bedrock_kb_execution_role_arn, suffix, identity
    encryption_policy, network_policy, access_policy = create_policies_in_oss(vector_store_name=vector_store_name,
                        aoss_client=aoss_client,
                        bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn,
                        suffix=suffix,
                        identity=identity
                        )
    
    return bedrock_kb_execution_role

#iam_client, collection_id, bedrock_kb_execution_role, suffix, account_number, region_name
def create_collection(iam_client, suffix, account_number, region_name, bedrock_kb_execution_role):
    aoss_client = boto3_session.client('opensearchserverless')
    collection = aoss_client.create_collection(name=VECTOR_STORE_NAME,type='VECTORSEARCH')

    # wait for collection creation
    # This can take couple of minutes to finish
    response = aoss_client.batch_get_collection(names=[VECTOR_STORE_NAME])
    # Periodically check collection status
    while (response['collectionDetails'][0]['status']) == 'CREATING':
        print('Creating collection...')
        interactive_sleep(30)
        response = aoss_client.batch_get_collection(names=[VECTOR_STORE_NAME])
    print('\nCollection successfully created:')
    pp.pprint(response["collectionDetails"])

    collection_arn = response["collectionDetails"][0]["arn"]
    collection_id = response["collectionDetails"][0]["id"]
    kb_host = collection_id + '.' + REGION + '.aoss.amazonaws.com'
    set_key('.env', "COLLECTION_ARN",collection_arn)
    set_key('.env', "COLLECTION_ID", collection_id)
    set_key('.env', "KB_HOST", kb_host)
#################
    try:
        #iam_client, collection_id, bedrock_kb_execution_role, suffix, account_number, region_name
        create_oss_policy_attach_bedrock_execution_role(iam_client=iam_client,
                                                        suffix=suffix,
                                                        account_number=account_number,
                                                        region_name=region_name,
                                                        collection_id=collection_id,
                                                        bedrock_kb_execution_role=bedrock_kb_execution_role)
        # It can take up to a minute for data access rules to be enforced
        interactive_sleep(60)
    except Exception as e:
        print("Policy already exists")
        pp.pprint(e)

################
if __name__ == "__main__":
    suffix = random.randrange(200, 900)
    set_key('.env', "SUFFIX", str(suffix))
    load_dotenv()
    REGION = os.getenv("REGION")
    S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME")
    VECTOR_STORE_NAME=os.getenv("COLLECTION_NAME") + f"-{suffix}"
    index_name = f"{VECTOR_STORE_NAME}-index"
    
    sts_client = boto3.client('sts')
    boto3_session = boto3.session.Session()
    iam_client = boto3_session.client('iam')
    identity = boto3.client('sts').get_caller_identity()['Arn']
    account_id = sts_client.get_caller_identity()["Account"]
    account_number = boto3.client('sts').get_caller_identity().get('Account')
    aoss_client = boto3_session.client('opensearchserverless')
    pp = pprint.PrettyPrinter(indent=2)

    #Create policies 
    bedrock_kb_execution_role = create_policies(iam_client=iam_client,
                                                bucket_name=S3_BUCKET_NAME, 
                                                region_name=REGION,
                                                account_number=account_number,
                                                suffix=suffix,
                                                identity=identity,
                                                vector_store_name=VECTOR_STORE_NAME
                                                )
    

    #Create collection
    create_collection(iam_client=iam_client,
                      suffix=suffix,
                      account_number=account_number, 
                      bedrock_kb_execution_role = bedrock_kb_execution_role,
                      region_name=REGION)
