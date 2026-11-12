from funnel.ai.base import Brain
from funnel.ai.mock import MockBrain
from funnel.ai.openai_adapter import OpenAIBrain
from funnel.settings import Settings, get_settings


def get_brain(settings: Settings | None = None) -> Brain:
    cfg = settings or get_settings()
    if cfg.use_real_llm:
        return OpenAIBrain(cfg)
    return MockBrain()
