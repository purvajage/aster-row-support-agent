from app.conversation import ConversationManager
from app.agent_workflow import (
    WorkflowResult,
    run_workflow,
)
from app.local_response import generate_policy_response


class SupportAgent:

    def __init__(
        self,
        conversation_manager=None,
    ):
        self.conversation_manager = (
            conversation_manager
            or ConversationManager()
        )

    def handle(
        self,
        session_id: str,
        message: str,
    ) -> WorkflowResult:

        # ---------------------------------------------------------
        # STORE USER MESSAGE
        # ---------------------------------------------------------

        self.conversation_manager.add_turn(
            session_id,
            "user",
            message,
        )

        # ---------------------------------------------------------
        # RUN DETERMINISTIC WORKFLOW
        # ---------------------------------------------------------

        result = run_workflow(
            self.conversation_manager,
            session_id,
            message,
        )

        # ---------------------------------------------------------
        # GENERATE RESPONSE ONLY WHEN WORKFLOW DID NOT
        # ---------------------------------------------------------
        #
        # Some workflow branches intentionally provide their own
        # deterministic, customer-safe answer:
        #
        # - TrailPlus
        # - international shipping
        # - Germany
        # - warranty
        # - standard return
        # - final-sale damaged item
        # - prompt injection
        # - insufficient information
        # - source conflict
        # - privacy refusal
        # - order lookup
        #
        # Never overwrite those answers.
        #
        if (
            result.action == "knowledge_retrieval"
            and not result.answer
        ):
            result.answer = generate_policy_response(
                result.retrieved_passages,
                message,
            )

        # ---------------------------------------------------------
        # STORE ASSISTANT RESPONSE
        # ---------------------------------------------------------

        if result.answer:
            self.conversation_manager.add_turn(
                session_id,
                "assistant",
                result.answer,
            )

        return result