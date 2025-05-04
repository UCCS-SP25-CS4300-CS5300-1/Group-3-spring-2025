import os
from openai import OpenAI

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

models = client.models.list()

print("Available models:")
for model in models.data:
    print("-", model.id)
