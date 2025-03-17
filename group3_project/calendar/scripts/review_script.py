
import os
import openai
import sys

# Example usage: python review_script.py "DIFF_CONTENT_HERE"
if __name__ == "__main__":
    openai.api_key = os.getenv("OPENAI_API_KEY")
    diff_content = sys.argv[1]  # The diff passed from the CI job

    # Basic prompt to OpenAI
    prompt = f"Perform a code review on the following diff:\n{diff_content}"

    response = client.responses.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful code review assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Print the response
    print(response['choices'][0]['message']['content'])