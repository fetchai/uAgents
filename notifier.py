import sys
import requests


def upload_file(api_token, channel_id, file_path, initial_comment=''):
    """
    Upload a file to a Slack channel using the Slack API.

    Args:
        api_token (str): Slack API token.
        channel_id (str): Channel ID or name where the file should be uploaded.
        file_path (str): Path to the file to be uploaded.
        initial_comment (str): Initial comment to be included with the file.

    Returns:
        bool: True if the file is uploaded successfully, False otherwise.
    """
    api_url = 'https://slack.com/api/files.upload'

    payload = {
        'channels': channel_id,
        'initial_comment': initial_comment,
    }

    headers = {
        'Authorization': f'Bearer {api_token}',
    }

    files = {
        'file': (open(file_path, 'rb')),
    }

    response = requests.post(api_url, data=payload, headers=headers, files=files)

    if response.status_code == 200:
        print(response.json())
        print(f"File uploaded to channel {channel_id}")
        return True
    else:
        print(f"Error uploading file: {response.text}")
        return False


def get_pr_details(owner, repo, pr_number):
    """
    Get details of a pull request from a GitHub repository.

    Args:
        owner (str): Owner of the GitHub repository.
        repo (str): Name of the GitHub repository.
        pr_number (int): Pull request number.

    Returns:
        dict or None: A dictionary containing details of the pull request if successful,
                      None otherwise.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(base_url)

    if response.status_code == 200:
        pr_details = response.json()
        return pr_details
    else:
        print("Error: Unable to fetch PR details. Status code:", response.status_code)
        return None

def notify_on_slack():
    pr_number =  sys.argv[1]
    owner = "fetchai"
    repo = "uAgents"
    pr_details = get_pr_details(owner, repo, pr_number)
    matching_files = [file['filename'] for file in pr_details if 'blog.md' in file['filename']]
    if len(matching_files):
        first_matching_file = matching_files[0]
        return first_matching_file
    else:
        return None
    
if __name__ == '__main__':
    slack_token= sys.argv[2]
    channel_id= sys.argv[3]
    path_response=notify_on_slack()
    file_path=path_response
    initial_comment = 'The integration has been successfully merged. Below is the content of the Markdown file associated with this integration.'
    upload_file(slack_token, channel_id, file_path, initial_comment)
