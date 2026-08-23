from dataclasses import dataclass, field


@dataclass
class ConversationTurn:
    role: str
    content: str


@dataclass
class ConversationSession:
    session_id: str
    turns: list[ConversationTurn] = field(
        default_factory=list
    )
    active_order_id: str | None = None
    last_topic: str | None = None


class ConversationManager:
    """
    Maintains isolated conversation sessions.

    Each session has its own history and relevant context.
    """

    def __init__(self, max_turns: int = 10):
        self.sessions: dict[str, ConversationSession] = {}
        self.max_turns = max_turns

    def get_session(
        self,
        session_id: str,
    ) -> ConversationSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id
            )

        return self.sessions[session_id]

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        session = self.get_session(session_id)

        session.turns.append(
            ConversationTurn(
                role=role,
                content=content,
            )
        )

        # Keep only recent conversation history.
        session.turns = session.turns[
            -self.max_turns:
        ]

    def set_order(
        self,
        session_id: str,
        order_id: str,
    ) -> None:
        session = self.get_session(session_id)
        session.active_order_id = order_id

    def get_order(
        self,
        session_id: str,
    ) -> str | None:
        return self.get_session(
            session_id
        ).active_order_id

    def set_topic(
        self,
        session_id: str,
        topic: str,
    ) -> None:
        session = self.get_session(session_id)
        session.last_topic = topic

    def get_topic(
        self,
        session_id: str,
    ) -> str | None:
        return self.get_session(
            session_id
        ).last_topic

    def get_recent_history(
        self,
        session_id: str,
        limit: int = 6,
    ) -> list[ConversationTurn]:
        session = self.get_session(session_id)

        return session.turns[-limit:]