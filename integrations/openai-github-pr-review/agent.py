import os
from typing import Tuple
from urllib.parse import urlparse

from ai_engine import UAgentResponse, UAgentResponseType
from codedog.actors.reporters.pull_request import PullRequestReporter
from codedog.chains import CodeReviewChain, PRSummaryChain
from codedog.retrievers import GithubRetriever
from github import Github
from github.GithubException import UnknownObjectException
from langchain.chat_models import ChatOpenAI
from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")
SEED_PHRASE = os.getenv("SEED_PHRASE")

agent = Agent(
    name="Github PR review AI Assistant",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())


class CodeReviewRequest(Model):
    """Model for handling code review requests."""

    pull_request_url: str


github_pr_review_protocol = Protocol("Github PR Review Automation")


def parse_github_pr_url(url: str) -> Tuple[bool, str, int]:
    p = urlparse(url)
    if p.netloc == "github.com":
        parts = p.path[1:].split("/")
        if len(parts) > 3 and parts[2] == "pull" and parts[3].isdigit():
            return True, "/".join(p.path[1:].split("/")[:2]), int(parts[3])
    return False, "", -1


def fetch_and_review_pull_request(pull_request_url, context: Context):
    """Fetches and reviews a GitHub pull request, returning a formatted report."""
    if not OPENAI_API_KEY:
        context.logger.error("OPENAI_API_KEY environment variables are not set.")
        return "Error: Missing environment variables."

    ok, repository, pull_request_number = parse_github_pr_url(pull_request_url)
    if not ok:
        msg = "🚫 Invalid Pull Request URL."
        context.logger.error(msg)
        return msg

    try:
        github_client = Github()
        retriever = GithubRetriever(github_client, repository, pull_request_number)
    except UnknownObjectException:
        msg = "🚫 Pull request not found. Check the repository and pull request number."
        context.logger.error(msg)
        return msg

    try:
        # PR Summary uses output parser
        llm35 = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")

        llm4 = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4")

        summary_chain = PRSummaryChain.from_llm(
            code_summary_llm=llm35, pr_summary_llm=llm4, verbose=True
        )
        summary = summary_chain(
            {"pull_request": retriever.pull_request}, include_run_info=True
        )

        context.logger.info(f"Summary: {summary}")

        review_chain = CodeReviewChain.from_llm(llm=llm35, verbose=True)
        reviews = review_chain(
            {"pull_request": retriever.pull_request}, include_run_info=True
        )

        context.logger.info(f"reviews: {reviews}")

        reporter = PullRequestReporter(
            pr_summary=summary["pr_summary"],
            code_summaries=summary["code_summaries"],
            pull_request=retriever.pull_request,
            code_reviews=reviews["code_reviews"],
        )

        report = reporter.report()
        context.logger.info(f"report: {report}")
        return report
    except Exception as exc:
        msg = f"🚫 An error occurred during the review process: {exc}"
        context.logger.error(msg)
        return msg


@github_pr_review_protocol.on_message(model=CodeReviewRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: CodeReviewRequest):
    """Processes code review requests and returns a formatted report or an error message."""
    report = fetch_and_review_pull_request(msg.pull_request_url, ctx)
    if "🚫" in report:
        response_message = report
        response_type = UAgentResponseType.ERROR
    else:
        response_message = f"✅ Code Review Completed Successfully:\n\n{report}"
        response_type = UAgentResponseType.FINAL

    await ctx.send(sender, UAgentResponse(message=response_message, type=response_type))


agent.include(github_pr_review_protocol, publish_manifest=True)
agent.run()
