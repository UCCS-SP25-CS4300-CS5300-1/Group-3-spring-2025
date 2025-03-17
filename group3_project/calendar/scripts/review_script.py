import os
from openai import OpenAI
import sys

if __name__ == "__main__":

    # Initialize the OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    diff_content = sys.argv[1]  # The diff passed from the CI job

    # Filter problematic Django template and JavaScript from the prompt
    filtered_lines = []
    for line in diff_content.split('\n'):
        if "{{" in line and "}}" in line:
            continue
        if ".tagsinput()" in line or "#autosaveStatus" in line:
            continue
        filtered_lines.append(line)
    
    # Join filtered lines into a single string
    filtered_diff = "\n".join(filtered_lines)

    # The prompt for the code review
    prompt = f"Perform a code review on the following diff:\n{filtered_diff}"

    # Call the API endpoint
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a helpful code review assistant.",
        input=prompt,
    )

    # Print the output from the AI
    print(response.output_text)
