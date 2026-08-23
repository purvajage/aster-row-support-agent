from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.prompts import SYSTEM_PROMPT


class LLMClient:
    """
    Small wrapper around the OpenAI API.

    If the API is unavailable because of quota or another
    provider error, the application can fall back to a
    deterministic response supplied by the workflow.
    """

    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def generate(
        self,
        user_context: str,
    ) -> str:
        """
        Generate an answer using the configured model.
        """
        response = self.client.responses.create(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=user_context,
        )

        return response.output_text