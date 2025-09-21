"""LLM configuration with LiteLLM support."""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


def get_llm_client(
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.1,
    max_tokens: int = 1000
):
    """Get LLM client with LiteLLM support."""
    
    use_litellm = os.getenv("USE_LITELLM", "false").lower() == "true"
    
    if use_litellm:
        # Use LiteLLM configuration
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("LITELLM_API_KEY"),
            openai_api_base=os.getenv("LITELLM_BASE_URL", "https://api.litellm.ai/v1")
        )
    
    # Standard provider configuration
    if model_name.startswith("gpt") or model_name.startswith("text-"):
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    elif model_name.startswith("claude"):
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    else:
        # Default to OpenAI-compatible via LiteLLM
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("LITELLM_API_KEY") if use_litellm else os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("LITELLM_BASE_URL") if use_litellm else None
        )