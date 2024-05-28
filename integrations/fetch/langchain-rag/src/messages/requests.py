from typing import Optional
from pydantic import Field
from uagents import Model


class RagRequest(Model):
    question: str = Field(
        description="The question that the user wants to have an answer for."
    )
    url: str = Field(description="The url of the docs where the answer is.")
    deep_read: Optional[str] = Field(
        description="Specifies weather all nested pages referenced from the starting URL should be read or not. The value should be yes or no.",
        default="no",
    )
