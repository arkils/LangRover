"""LLM provider factory for swappable language models."""

import os
import urllib.request

from langchain_openai import ChatOpenAI


def _check_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = urllib.request.urlopen(f"{base_url}/api/tags", timeout=2)
        return response.status == 200
    except Exception:
        return False


def get_llm(provider: str = "openai"):
    """
    Get a LangChain *chat* model instance that supports ``bind_tools()``.

    All returned models are Chat LLMs (not completion LLMs), which is required
    for LangChain tool calling (``llm.bind_tools(tools)``).

    Args:
        provider: One of ``"openai"``, ``"ollama"``.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If provider is not supported.
        ConnectionError: If Ollama is selected but not running.
        ImportError: If required dependencies are missing.
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it with: $env:OPENAI_API_KEY='sk-...'"
            )
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=api_key,
        )

    elif provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for Ollama support. "
                "Install with: pip install langchain-ollama"
            )

        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:270m")

        print(f"Checking Ollama connection at {ollama_base_url}...")
        if not _check_ollama_connection(ollama_base_url):
            raise ConnectionError(
                f"Ollama is not running at {ollama_base_url}. "
                f"Start Ollama with: ollama serve\n"
                f"Or set OLLAMA_BASE_URL to your Ollama instance."
            )

        print(f"[OK] Connected to Ollama at {ollama_base_url}")
        print(f"[OK] Using model: {ollama_model}")

        return ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Supported: 'openai', 'ollama'"
        )
