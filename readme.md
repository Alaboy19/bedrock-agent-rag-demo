## Pre-requesites:
1. Install Python 
```sh
brew install python
 ``` 
2. Install poetry
```sh
brew install poetry
 ``` 

## Setup poetry

1. command: 
```sh
poetry install 
 ```   
2. command:
```sh 
poetry self add poetry-plugin-shell
 ```   

3. Activate the virtual environment with 
```sh 
poetry shell 
 ```  
## Set up aws account and aws credentials. 
1. Setup aws account and account role and give access to services  with IAM from [policies.txt](http://_vscodecontentref_/3)
2. create aws account user and give these permissions with IAM to get access to bedrock [policies.txt](http://_vscodecontentref_/3)


## Setup your aws credentials
```sh 
aws confgiure 
  ``` 

## Env variables 
Create .env variables and set these:
1. REGION=region, in my case - 'us-east-1'
2. AGENT_NAME=name of your agent
3. S3_BUCKET_NAME=name of your s3 bucket
4. FOUNDATION_MODEL='us.anthropic.claude-3-5-haiku-20241022-v1:0', the model to which you get access under your agent role below
5. AGENT_RESOURCE_ROLE_ARN = agent_role resource name that you have created 

# Execution Stages. 

## Stage 1. Create S3 bucket and upload docs and creates lambda function for agent logic
```sh 
./upload_and_create.sh
 ``` 
## Stage 2. Create knowledgebase from these docs 

Ideally run following command, but could not managed to finish this part on time, so just used console for that.
```sh 
python3 src/create_kb.py 
 ``` 
So, follow steps in creating kb in aws bedrock console in [here](http://_vscodecontentref_/7)

## Stage 3. Build agent 
```sh 
python src/agent_build.py 
 ```

Agent_build.py returns kb_id and agent_id that is passed to src/agent_chat.py

## Stage 4. Create CLI interaction
```sh 
 python src/agent_build.py
  ```

This initates the CLI chat with agent that has some limited capabilites for demo.
