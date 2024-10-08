import requests

from uagents import Context, Protocol, Model
from ai_engine import UAgentResponse, UAgentResponseType

class Username(Model):
  username: str

github_user_protocol = Protocol("GitHub User Protocol")

def fetch_user_repositories(username):
  url = f"https://api.github.com/users/{username}/repos"

  try:
    response = requests.get(url)
    response.raise_for_status()
    repositories = response.json()

    # sort repositories by 'most recently contributed to'
    sorted_repositories = sorted(repositories, key=lambda repo: repo['pushed_at'], reverse=True)

    repo_names = [(repo['name'], repo['description'] or "No description provided") for repo in sorted_repositories]

    repository_names = []
    for name, description in repo_names:
      repository_names.append(f"{name}: {description}")
    response = '\n'.join(repository_names)
    return response

  except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")
  except Exception as err:
    print(f"An error occurred: {err}")



@github_user_protocol.on_message(model=Username, replies={UAgentResponse})
async def get_repository_names(ctx: Context, sender: str, msg: Username):
  ctx.logger.info("Querying all public repositories for " + msg.username)
  repositories = fetch_user_repositories(msg.username)
  await ctx.send(sender, UAgentResponse(message=repositories, type=UAgentResponseType.FINAL))

agent.include(github_user_protocol, publish_manifest=True)
