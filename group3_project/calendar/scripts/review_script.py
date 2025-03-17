import os
from openai import OpenAI
import sys

if __name__ == "__main__":

    #initialize the OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    diff_content = sys.argv[1]  #The diff passed from the CI job

    #the prompt for the code review
    prompt = f"Perform a code review on the following diff:\n{diff_content}"

    #call the API endpoint (client.responses.create)
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a helpful code review assistant.",
        input=prompt,
    )

    #print the output from the AI
    print(response.output_text)