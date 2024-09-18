import requests
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field

# Get the API key
token = "YOUR_GITHUB_TOKEN"


class Org_name(Model):
    org_name: str = Field("Please enter the name of your organisation.")


github_protocol = Protocol("Github Protocol")


async def fetch_github_repos(org_name, token):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    params = {
        "per_page": 100  # You can adjust this number (max is 100)
    }

    all_repos = []

    while url:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            repos = response.json()
            all_repos.extend(repos)

            # Check if there is a 'next' page
            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None
        else:
            print(
                f"Failed to fetch repositories: {response.status_code} - {response.text}"
            )
            break

    return all_repos


async def print_repos(repos):
    repo_names = []
    for repo in repos:
        repo_names.append(repo["name"])
    return "\n".join(repo_names)


@github_protocol.on_message(model=Org_name, replies={UAgentResponse})
async def get_repo_names(ctx: Context, sender: str, msg: Org_name):
    ctx.logger.info(msg.org_name)

    all_repos = await fetch_github_repos(msg.org_name, token)
    repo_names = await print_repos(all_repos)
    await ctx.send(
        sender, UAgentResponse(message=repo_names, type=UAgentResponseType.FINAL)
    )


agent.include(github_protocol, publish_manifest=True)
