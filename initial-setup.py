import openai
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment variable
api_key = os.getenv('OPENAI_API_KEY')

# Set the API key for the OpenAI client
openai.api_key = api_key

# print(os.environ)

# response = openai.chat.completions.create(model='gpt-4o',messages=[{"role":"user","content":"what is tesla"}])
# print(response)


messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, who are you?"},
    {"role": "assistant", "content": "I am an AI created by OpenAI. How can I assist you today?"},
    {"role": "user", "content": "Can you tell me what RAG in LLM stands for?"}
]

# Create a chat completion
response = openai.chat.completions.create(
    model='gpt-4o',
    messages=messages
)

# Extract and print the assistant's reply
# Extract and print the assistant's reply
assistant_reply = response.choices[0].message.content
print(assistant_reply)
