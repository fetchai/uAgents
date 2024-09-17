import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model
from pydantic import Field

class Github_User_Query(Model):
    username: str = Field("Please enter the username of the Github account to query.")
    token: str = Field("Please enter your Github token.")

github_contribution_protocol = Protocol("Github User Contribution Protocol")

async def fetch_github_user_contributions(username, token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    query = f"""{{
                user(login:"{username}") {{
                    repositoriesContributedTo(contributionTypes:COMMIT, first:100) {{
                        nodes {{
                            name
                        }}
                    }}
                }}
            }}"""
    print(query)

    response = requests.post(url, headers=headers, json={"query": query})

    try:
        return list(map(lambda x: x["name"], response.json()["data"]["user"]["repositoriesContributedTo"]["nodes"]))
    except:
        return []

@github_contribution_protocol.on_message(model=Github_User_Query, replies={UAgentResponse})
async def get_repo_names(ctx: Context, sender: str, msg: Github_User_Query):
    ctx.logger.info(f"Fetching user contributions for {msg.username}")

    repos = await fetch_github_user_contributions(msg.username, msg.token)

    if len(repos) == 0:
        rsp = f"{msg.username} has not contributed to any external repositories or we encountered an issue."
    else:
        rsp = f"{msg.username} has contributed {len(repos)} external repositories:\n{"\n".join(repos)}"
    await ctx.send(sender, UAgentResponse(message=rsp, type= UAgentResponseType.FINAL))

agent = Agent("Contribution Agent", seed="contribution agent seed phrase")
agent.include(github_contribution_protocol, publish_manifest=True)
agent.run()