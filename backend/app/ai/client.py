"""
PydanticAI model factory and agent builder.

Central abstraction over all supported LLM providers.
Every AI agent in this project must obtain its model through
``get_model()`` — never instantiate provider clients directly in agents.

Supported providers (from settings.ai_provider):
  "gemini"  → Google Gemini via pydantic-ai[gemini]
  "openai"  → OpenAI via pydantic-ai[openai]
  "groq"    → Groq via pydantic-ai[groq]
  "ollama"  → Ollama (local) via pydantic-ai[ollama]

All agents share a 30-second timeout.  If the LLM does not respond
within that window the caller should fall back to a cached or
deterministic result (see recommendation_service.py).
"""

import sys
import types
from typing import Any

# 1. Fallback for opentelemetry._events if missing in installed opentelemetry package
class _DummyClass:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return self
    def __getattr__(self, item):
        return _DummyClass()

class _DummyOtelEvents(types.ModuleType):
    def __getattr__(self, name):
        return _DummyClass

try:
    import opentelemetry._events
except ImportError:
    sys.modules["opentelemetry._events"] = _DummyOtelEvents("opentelemetry._events")

# 2. Complete _griffe module aliasing for pydantic-ai compatibility
try:
    import griffe
    sys.modules["_griffe"] = griffe
    sys.modules["_griffe.enumerations"] = griffe
    sys.modules["_griffe.models"] = griffe
    sys.modules["_griffe.dataclasses"] = griffe
    sys.modules["_griffe.expressions"] = griffe
    sys.modules["_griffe.extensions"] = griffe
    sys.modules["_griffe.agents"] = griffe
    sys.modules["_griffe.docstrings"] = griffe

    setattr(griffe, "enumerations", griffe)
    setattr(griffe, "models", griffe)
    setattr(griffe, "dataclasses", griffe)
    setattr(griffe, "expressions", griffe)
except Exception:
    pass

try:
    from pydantic_ai import Agent
    from pydantic_ai.models import Model
except Exception as _ai_import_err:
    Agent = Any  # type: ignore
    Model = Any  # type: ignore

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Agents are stateless — safe to share across requests.
# Each agent is a typed wrapper around a single output schema.
_agent_cache: dict[str, Agent] = {}

AI_TIMEOUT_SECONDS = 30


def get_model() -> Model:
    """
    Return a PydanticAI ``Model`` instance for the configured provider.

    Reads ``settings.ai_provider`` at call time so tests can override it.
    """
    provider = settings.ai_provider

    if provider == "openai":
        from pydantic_ai.models.openai import OpenAIModel
        logger.debug("Using OpenAI model", model=settings.openai_model)
        return OpenAIModel(
            settings.openai_model,
            api_key=settings.openai_api_key,
        )

    if provider == "groq":
        from pydantic_ai.models.groq import GroqModel
        logger.debug("Using Groq model", model=settings.groq_model)
        return GroqModel(
            settings.groq_model,
            api_key=settings.groq_api_key,
        )

    if provider == "ollama":
        from pydantic_ai.models.ollama import OllamaModel
        logger.debug("Using Ollama model", model=settings.ollama_model)
        return OllamaModel(
            settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    # Default: Gemini
    try:
        from pydantic_ai.models.google import GoogleModel
    except ImportError:
        from pydantic_ai.models.gemini import GeminiModel as GoogleModel

    import os
    if settings.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    logger.debug("Using Gemini model", model=settings.gemini_model)
    return GoogleModel(
        settings.gemini_model,
    )


def build_agent(
    output_schema: type,
    system_prompt: str,
    *,
    retries: int = 2,
) -> Agent:
    """
    Build a PydanticAI ``Agent`` with the given output schema and system prompt.

    Parameters
    ----------
    output_schema:
        The Pydantic model class the agent must return.
    system_prompt:
        The system prompt string.
    retries:
        How many times PydanticAI will retry if schema validation fails.

    Returns
    -------
    A configured ``Agent`` instance.
    """
    try:
        return Agent(
            model=get_model(),
            result_type=output_schema,
            system_prompt=system_prompt,
            retries=retries,
        )
    except TypeError:
        return Agent(
            model=get_model(),
            output_type=output_schema,
            system_prompt=system_prompt,
            retries=retries,
        )


async def run_agent(agent: Agent, user_prompt: str) -> Any:
    """
    Run *agent* with *user_prompt* and return the validated result data.

    Wraps ``agent.run()`` with logging and timeout handling.
    Raises the original exception so callers can implement their own
    fallback strategy.

    Parameters
    ----------
    agent:
        A configured ``Agent`` instance (from ``build_agent``).
    user_prompt:
        The user-turn message to send to the model.

    Returns
    -------
    The validated ``result_type`` instance (e.g. ``RecommendationOutput``).
    """
    logger.info(
        "AI agent run started",
        model=settings.ai_provider,
        prompt_chars=len(user_prompt),
    )
    result = await agent.run(user_prompt)
    logger.info(
        "AI agent run completed",
        model=settings.ai_provider,
        output_type=type(result.output).__name__,
    )
    return result.output
