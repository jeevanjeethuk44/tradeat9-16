# 🚀 Setting Up Your Gemini Code Review Action

Congratulations on setting up the Gemini Code Review GitHub Action! To get it working, you need to provide it with secure credentials to access the Gemini API and post comments to your pull requests.

This is done by creating **two secrets** in your GitHub repository settings.

## Required Secrets

1.  `GEMINI_API_KEY`: To authenticate with the Google Gemini API.
2.  `GITHUB_TOKEN`: To allow the action to post comments on your pull requests.

---

## Step 1: Create a Gemini API Key

1.  **Go to Google AI Studio:** Open your web browser and navigate to [Google AI Studio](https://aistudio.google.com/).
2.  **Sign in:** Use your Google account to sign in.
3.  **Get API Key:**
    *   Click on the "**Get API key**" button in the top left corner.
    *   In the dialog that appears, click "**Create API key**".
    *   Your new API key will be generated. **Copy this key immediately** and save it somewhere safe temporarily. You will not be able to see it again.

---

## Step 2: Create a GitHub Personal Access Token (PAT)

The built-in `secrets.GITHUB_TOKEN` has some limitations. For maximum reliability, it's best to create a personal access token.

1.  **Go to GitHub Developer Settings:**
    *   Click on your profile picture in the top right of GitHub and go to **Settings**.
    *   On the left sidebar, scroll down and click on **Developer settings**.
    *   Click on **Personal access tokens**, then **Tokens (classic)**.
2.  **Generate a new token:**
    *   Click the "**Generate new token**" button.
    *   Give your token a descriptive name, like `gemini-review-action`.
    *   Set the **Expiration** to your desired duration (e.g., 90 days).
    *   In the "**Select scopes**" section, check the box for **`repo`**. This will grant the necessary permissions for the action to read repository content and write comments to pull requests.
    *   Scroll down and click "**Generate token**".
3.  **Copy your new token:** **Copy the token immediately.** Just like the Gemini key, you won't be able to see it again.

---

## Step 3: Add the Keys as Repository Secrets

Now, you need to add the two keys you just created to your repository's secrets.

1.  **Go to your repository's settings:** In your repository on GitHub, click the "**Settings**" tab.
2.  **Navigate to Secrets:** On the left sidebar, click on "**Secrets and variables**", then "**Actions**".
3.  **Add the Gemini API Key:**
    *   Click the "**New repository secret**" button.
    *   For the **Name**, enter `GEMINI_API_KEY`.
    *   In the **Value** box, paste the Gemini API key you copied earlier.
    *   Click "**Add secret**".
4.  **Add the GitHub Token:**
    *   Click "**New repository secret**" again.
    *   For the **Name**, enter `GITHUB_TOKEN`.
    *   In the **Value** box, paste the GitHub Personal Access Token you created.
    *   Click "**Add secret**".

---

## ✅ You're All Set!

That's it! The next time you open a pull request in this repository, the Gemini Code Review action should run automatically. You will see the review posted as a comment from the user whose Personal Access Token you used.
