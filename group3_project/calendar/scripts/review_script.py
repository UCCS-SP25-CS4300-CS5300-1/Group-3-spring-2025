import os
from openai import OpenAI
import sys
import re

def clean_diff(diff_content):
    # Regular expression to remove Django template tags like {{ ... }}
    clean_content = re.sub(r'\{\{.*?\}\}', '', diff_content)  # Removes {{ ... }}
    return clean_content

if __name__ == "__main__":

    #initialize the OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    diff_content = sys.argv[1]
    clean_diff_content = clean_diff(diff_content)
    prompt = f"Perform a code review on the following diff:\n{clean_diff_content}"

    #call the API endpoint (client.responses.create)
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a helpful code review assistant.",
        input=prompt,
    )

    #print the output from the AI
    print(response.output_text)
