import os
from openai import OpenAI
import sys

if __name__ == "__main__":
    # Initialize the OpenAI client using the new API interface
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    diff_content = sys.argv[1]  # The diff passed from the CI job

    # Build the prompt for the code review
    prompt = f"Perform a code review on the following diff:\n{diff_content}"

    # Call the new API endpoint (client.responses.create) with updated parameters
    response = client.responses.create(
        model="gpt-4o",  # Using the model specified in the README (change if needed)
        instructions="You are a helpful code review assistant.",
        input=prompt,
    )

    # Print the output from the AI
    print(response.output_text)
