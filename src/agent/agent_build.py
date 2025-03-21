import os
import boto3
import json
import time
from dotenv import load_dotenv, set_key
from utils import wait_for_agent_status, wait_for_agent_alias_status, wait_for_action_group_status


# Load environment variables from .env file
load_dotenv()
REGION = os.getenv("REGION")
AGENT_NAME = os.getenv("AGENT_NAME")
FOUNDATION_MODEL = os.getenv("FOUNDATION_MODEL")
AGENT_RESOURCE_ROLE_ARN = os.getenv("AGENT_RESOURCE_ROLE_ARN")
LAMBDA_FUNCTION_ARN = os.getenv("LAMBDA_FUNCTION_ARN")

# Read instructions
with open("src/agent/instruction.txt", "r", encoding="utf-8") as file:
    instructions = file.read()

with open('src/agent/action_group.json', 'r', encoding='utf-8') as file:
    function_schema = json.load(file)


def agent_builder():
    bedrock_agent = boto3.client(service_name="bedrock-agent", region_name=REGION)
    create_agent_response = bedrock_agent.create_agent(
        agentName=AGENT_NAME,
        foundationModel=FOUNDATION_MODEL,
        instruction=instructions,
        agentResourceRoleArn=AGENT_RESOURCE_ROLE_ARN,
    )
    agentId = create_agent_response["agent"]["agentId"]
    print(f"\nCreated agent with ID: {agentId}\n")
    time.sleep(5)

    #integrate with knowledge base

    response = bedrock_agent.list_knowledge_bases()
    kb_id = None

    for kb in response["knowledgeBaseSummaries"]:
        kb_id = kb["knowledgeBaseId"]

    print(f"\nFound knowledge base with ID: {kb_id}\n")

    bedrock_agent.associate_agent_knowledge_base(
        agentId=agentId,
        knowledgeBaseId=kb_id,
        agentVersion="DRAFT",
        description="Associate agent with knowledge base",
    )
    print(f"\nAssociated agent {agentId} with knowledge base {kb_id}\n")

    # action group
    create_agent_action_group_response = bedrock_agent.create_agent_action_group(
    actionGroupName='additional-support-actions',
    agentId=agentId,
    actionGroupExecutor={
        'lambda': LAMBDA_FUNCTION_ARN
    },
    functionSchema=function_schema,
    agentVersion='DRAFT',
    )

    actionGroupId = create_agent_action_group_response['agentActionGroup']['actionGroupId']

    wait_for_action_group_status(
    agentId=agentId, 
    actionGroupId=actionGroupId,
    targetStatus='ENABLED'
    )
    print(f"\nAction group {actionGroupId} is enabled\n")

     # action group - Code interpreter for date 

    create_agent_action_group_response = bedrock_agent.create_agent_action_group(
    actionGroupName='CodeInterpreterAction',
    actionGroupState='ENABLED',
    agentId=agentId,
    agentVersion='DRAFT',
    parentActionGroupSignature='AMAZON.CodeInterpreter'
    )

    codeInterpreterActionGroupId = create_agent_action_group_response['agentActionGroup']['actionGroupId']

    wait_for_action_group_status(
        agentId=agentId, 
        actionGroupId=codeInterpreterActionGroupId
    )

    print(f"\nCode Interpreter action group {codeInterpreterActionGroupId} is enabled\n")

    # prepare agent    
    bedrock_agent.prepare_agent(agentId=agentId)

    wait_for_agent_status(agentId=agentId, targetStatus="PREPARED")
    print(f"\nAgent {agentId} is prepared\n")

    return agentId


def agent_alias_builder(agentId):
    bedrock_agent = boto3.client(service_name="bedrock-agent", region_name="us-east-1")
    create_agent_alias_response = bedrock_agent.create_agent_alias(
        agentId=agentId,
        agentAliasName="MyAgentAlias",
    )

    agentAliasId = create_agent_alias_response["agentAlias"]["agentAliasId"]
    print(f"Created agent alias with ID: {agentAliasId}")

    wait_for_agent_alias_status(
        agentId=agentId, agentAliasId=agentAliasId, targetStatus="PREPARED"
    )
    print(f"Agent alias {agentAliasId} is prepared")
    return agentAliasId


def main():
    agentId = agent_builder()
    agentAliasId = agent_alias_builder(agentId)

    output_data = {"agentId": agentId, "agentAliasId": agentAliasId}
    print(json.dumps(output_data))

    set_key('.env', "AGENT_ID", agentId)
    set_key('.env', "AGENT_ALIAS_ID", agentAliasId)


if __name__ == "__main__":
    main()

