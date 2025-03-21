import os
import uuid
from dotenv import load_dotenv
from utils import invoke_agent_and_print


load_dotenv()
AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS_ID=os.getenv("AGENT_ALIAS_ID")

# Generate a unique session ID for the chat session
SESSION_ID = str(uuid.uuid4())


if __name__ == "__main__":
    print("Welcome to your Bedrock CLI Chat! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = invoke_agent_and_print(
            AGENT_ID, AGENT_ALIAS_ID, inputText=user_input, sessionId=SESSION_ID
        )
        # response = chat_with_agent(
        #     agentId=AGENT_ID, agentAliasId=AGENT_ALIAS_ID, user_input=user_input, sessionId=SESSION_ID
        # )
        print(f"Agent: {response}")
