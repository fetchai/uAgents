from pydantic import Field
from uagents import Model


class NotionRequest(Model):
    feedback_title: str = Field(
        description="Feedback title that the user wants to use to create a new Notion feedback. User MUST specify it, don't pre fill it."
    )
