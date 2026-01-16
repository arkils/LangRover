"""LLM provider factory for swappable language models."""

import os
import urllib.request
from typing import Union

from langchain_openai import ChatOpenAI


def _check_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama is running and accessible.

    Args:
        base_url: URL where Ollama is running.

    Returns:
        True if Ollama is accessible, False otherwise.
    """
    try:
        response = urllib.request.urlopen(f"{base_url}/api/tags", timeout=2)
        return response.status == 200
    except Exception:
        return False


def get_llm(provider: str = "openai"):
    """
    Get a language model instance.

    Centralized factory for LLM instantiation. This allows easy switching
    between providers without modifying agent or other logic.

    Args:
        provider: LLM provider name ("openai" or "ollama").

    Returns:
        A LangChain language model instance.

    Raises:
        ValueError: If provider is not supported.
        ConnectionError: If Ollama is selected but not running.
        ImportError: If required dependencies are missing.
    """
    if provider == "openai":
        # Using GPT-4o-mini for cost-effective inference
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it with: $env:OPENAI_API_KEY='sk-...'"
            )

        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,  # Deterministic behavior for consistent decisions
            api_key=api_key,
        )

    elif provider == "ollama":
        # Local Ollama model support
        try:
            from langchain_community.llms import Ollama
        except ImportError:
            raise ImportError(
                "langchain-community is required for Ollama support. "
                "Install with: pip install langchain-community"
            )

        # Get configuration from environment or use defaults
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:270m")

        # Verify Ollama is running before creating the client
        print(f"Checking Ollama connection at {ollama_base_url}...")
        if not _check_ollama_connection(ollama_base_url):
            raise ConnectionError(
                f"Ollama is not running at {ollama_base_url}. "
                f"Start Ollama with: ollama serve\n"
                f"Or set OLLAMA_BASE_URL to your Ollama instance."
            )

        print(f"[OK] Connected to Ollama at {ollama_base_url}")
        print(f"[OK] Using model: {ollama_model}")

        return Ollama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: 'openai', 'ollama'"
        )
