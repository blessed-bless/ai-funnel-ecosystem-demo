from dataclasses import dataclass
from typing import Protocol


@dataclass
class AIReply:
    text: str
    name: str = ""
    contact: str = ""
    interest: str = ""
    summary: str = ""
    ready_to_submit: bool = False


class Brain(Protocol):
    async def reply(self, history: list[dict[str, str]], user_message: str) -> AIReply:
        """Return assistant text and optional structured lead draft."""
