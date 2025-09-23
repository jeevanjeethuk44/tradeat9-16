import os
import requests
import google.generativeai as genai

# --- Configuration ---
# Get credentials and context from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")
PR_DIFF = os.getenv("PR_DIFF")

# --- System Prompt for Gemini ---
SYSTEM_PROMPT = """
You are an expert software engineer acting as a code reviewer.
Your task is to provide a concise, high-level code review for the given pull request diff.

Instructions:
1.  **Analyze the diff:** Identify potential bugs, style issues, and areas for improvement.
2.  **Be concise:** Provide a brief summary of your findings. Do not comment on every single line. Focus on the most important issues.
3.  **Use Markdown:** Format your review using Markdown for readability.
4.  **Friendly Tone:** Start with a friendly opening.
5.  **No Diff Recap:** Do not simply repeat the code changes from the diff. Assume the user has already seen the diff.
6.  **Sign-off:** End with a "Happy coding!" sign-off.

Example:
"Hi there! Here's a quick review of your changes:
*   The new function `calculate_interest` looks good, but it might be more efficient to move the `rate` calculation outside the loop.
*   There's a potential off-by-one error in the `for` loop in `update_prices`.
*   Consider adding a docstring to the `connect_api` function to explain its purpose.

Happy coding!"
"""

def post_github_comment(message):
    """Posts a comment to the GitHub pull request."""
    if not all([GITHUB_REPO, PR_NUMBER, GITHUB_TOKEN]):
        print("Error: Missing GitHub environment variables for posting comment.")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": message}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print("Successfully posted review comment to GitHub.")
    except requests.exceptions.RequestException as e:
        print(f"Error posting comment to GitHub: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")

def main():
    """Main function to run the code review."""
    # 1. Validate environment variables
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set.")
        return

    if not PR_DIFF or PR_DIFF.strip() == "":
        print("Diff is empty. No code to review.")
        return

    # 2. Configure Gemini API
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        post_github_comment(f"Sorry, I couldn't run the review. There was an issue connecting to the Gemini API: `{e}`")
        return

    # 3. Construct the prompt
    prompt = f"{SYSTEM_PROMPT}\\n\\nHere is the pull request diff to review:\\n```diff\\n{PR_DIFF}\\n```"

    # 4. Call the Gemini API
    try:
        print("Generating code review with Gemini...")
        response = model.generate_content(prompt)
        review_text = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        post_github_comment(f"Sorry, I couldn't run the review. There was an error generating the review from Gemini: `{e}`")
        return

    # 5. Post the review to GitHub
    print("Code review generated. Posting to GitHub.")
    post_github_comment(review_text)

if __name__ == "__main__":
    main()
