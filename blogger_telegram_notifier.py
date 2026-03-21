#!/usr/bin/env python3

import requests
import xml.etree.ElementTree as ET
import os
import json

# --- Configuration --- #
BLOGGER_RSS_FEED_URL = os.environ.get("BLOGGER_RSS_FEED_URL")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# GitHub Actions specific environment variables
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY") # e.g., "username/repo_name"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # Token with repo scope

# File to store the last published post's link within the GitHub repository
LAST_POST_FILENAME = "last_blogger_post.json"

def get_latest_post(feed_url):
    """Fetches the RSS feed and returns the latest post's title and link."""
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        root = ET.fromstring(response.content)

        # Blogger RSS feeds are Atom 1.0, so we need to use Atom namespaces
        # Find the latest entry (post)
        latest_entry = root.find("{http://www.w3.org/2005/Atom}entry")
        if latest_entry:
            title_element = latest_entry.find("{http://www.w3.org/2005/Atom}title")
            title = title_element.text if title_element is not None else "No Title"
            link_element = latest_entry.find("{http://www.w3.org/2005/Atom}link[@rel=\"alternate\"]")
            link = link_element.attrib["href"] if link_element is not None else "#"
            return title, link
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
    except ET.ParseError as e:
        print(f"Error parsing RSS feed: {e}")
    return None, None

def send_telegram_message(bot_token, chat_id, message):
    """Sends a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" # Use HTML for rich text formatting
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def get_github_file_content(repo, path, token):
    """Gets content of a file from GitHub repository."""
    headers = {"Authorization": f"token {token}"}
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = requests.get(api_url, headers=headers, timeout=10)
    if response.status_code == 200:
        content = response.json()["content"]
        # GitHub API returns base64 encoded content
        import base64
        return base64.b64decode(content).decode("utf-8"), response.json()["sha"]
    return None, None

def update_github_file_content(repo, path, token, content, sha, message):
    """Updates content of a file in GitHub repository."""
    headers = {"Authorization": f"token {token}"}
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    import base64
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": message,
        "content": encoded_content,
        "sha": sha
    }
    response = requests.put(api_url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    print(f"GitHub file {path} updated successfully.")

def main():
    if not all([BLOGGER_RSS_FEED_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITHUB_REPOSITORY, GITHUB_TOKEN]):
        print("Error: Please set BLOGGER_RSS_FEED_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITHUB_REPOSITORY, and GITHUB_TOKEN environment variables.")
        return

    print("Checking for new Blogger posts...")
    latest_title, latest_link = get_latest_post(BLOGGER_RSS_FEED_URL)

    if latest_link:
        # Get last known post link from GitHub repository
        last_post_data_str, sha = get_github_file_content(GITHUB_REPOSITORY, LAST_POST_FILENAME, GITHUB_TOKEN)
        last_known_link = None
        if last_post_data_str:
            try:
                last_post_data = json.loads(last_post_data_str)
                last_known_link = last_post_data.get("last_link")
            except json.JSONDecodeError:
                print("Error decoding last_blogger_post.json. Initializing with current link.")

        if latest_link != last_known_link:
            message = f"<b>새 블로그 글 발행!</b>\n\n제목: {latest_title}\n링크: <a href=\"{latest_link}\">{latest_link}</a>"
            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

            # Update last known post link in GitHub repository
            new_post_data = {"last_link": latest_link}
            new_post_data_str = json.dumps(new_post_data)
            if sha:
                update_github_file_content(GITHUB_REPOSITORY, LAST_POST_FILENAME, GITHUB_TOKEN, new_post_data_str, sha, "Update last blogger post link")
            else:
                # If file doesn't exist, create it (GitHub API requires a SHA for update, not create)
                # This case is handled by get_github_file_content returning None for sha
                # For simplicity, we'll assume the file exists after the first run or create it manually once.
                # A more robust solution would involve checking for file existence and creating if not present.
                print(f"Warning: {LAST_POST_FILENAME} not found. Please create it manually in your repository with {{'last_link': ''}} or similar content for the first run.")
                # As a workaround for the first run, if the file doesn't exist, we can try to create it.
                # However, GitHub API for 'create file' is different from 'update file'.
                # For this example, we'll rely on the user creating an empty JSON file initially.
                # If sha is None, it means the file didn't exist, so we can't update it with PUT.
                # The user will need to manually create an empty last_blogger_post.json in the repo.
                pass # The script will proceed, but persistence won't work until the file is created.
        else:
            print("No new posts found.")
    else:
        print("Could not retrieve latest post information.")

if __name__ == "__main__":
    main()
