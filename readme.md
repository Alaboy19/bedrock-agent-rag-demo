## Pre-requesites(assuming you have brew installed)
1. Install Python(if you don't have one) 
```sh
brew install python
 ``` 
2. Install poetry (poetry is is a dependency management and packaging tool for Python that simplifies project setup, handles virtual environments, and ensures consistent builds with a pyproject.toml configuration file)
```sh
brew install poetry
 ``` 

## Setup poetry

1. Install dependencies(alternatively you can use pip install -r requriements.txt, in case you do not prefer to use poetry): 
```sh
poetry install --no-root
 ```   
2. command:
```sh 
poetry self add poetry-plugin-shell
 ```   

3. Create or activate the virtual environment(if already exists) with 
```sh 
poetry shell 
 ```  
## Set up aws account and aws credentials. 
1. Setup aws account and account role and give access to services  with IAM from [policies.txt](policies.txt)
2. Create role for bedrock agent and give these permissions with IAM to get access to bedrock [policies.txt](policies.txt)


## Setup your aws credentials
Set up credentials for created aws account to which the account role is given in prev step, point 1, you need to generate access key for this account to be able to use aws cli 
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
python3 src/kb/create_kb.py 
 ``` 
So, follow steps in creating kb in aws bedrock console in [here](kb_console.txt)

## Stage 3. Build agent 
Agent_build.py returns knowledebase_id and agent_id and sets them as env variable
```sh 
python src/agent/agent_build.py 
 ```

## Stage 4. Create CLI interaction
This initates the CLI chat with agent that has some limited capabilites for demo.
```sh 
 python src/agent/agent_chat.py
  ```

## Diagram 
![Screenshot 2025-03-21 at 12.11.06.png]()




