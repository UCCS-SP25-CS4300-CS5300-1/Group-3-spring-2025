
import os
import openai
import sys

# Example usage: python review_script.py "DIFF_CONTENT_HERE"
if __name__ == "__main__":
    openai.api_key = os.getenv("OPENAI_API_KEY")
    diff_content = sys.argv[1]  # The diff passed from the CI job

    # Filter problematic Django template and JavaScript from the prompt
    filtered_lines = []
    for line in diff_content.split('\n'):
        if "{{" in line and "}}" in line:
            continue
        if ".tagsinput()" in line or "#autosaveStatus" in line:
            continue
        filtered_lines.append(line)
    
    filtered_diff = "\n".join(filtered_lines)

    # Basic prompt to OpenAI
    prompt = f"Perform a code review on the following diff:\n{filtered_lines}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful code review assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Print the response
    print(response['choices'][0]['message']['content'])
