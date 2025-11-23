"""LiteLLM client for making LLM requests to any provider."""

import asyncio
from typing import List, Dict, Any, Optional
from litellm import acompletion
import openai


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    reasoning_effort: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via LiteLLM.

    Args:
        model: LiteLLM model identifier with provider prefix
               (e.g., "openai/gpt-5.1", "anthropic/claude-3-5-sonnet-20241022")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        reasoning_effort: Reasoning effort level ("none", "low", "medium", "high")
                         LiteLLM translates to provider-specific params

    Returns:
        Response dict with 'content', optional 'reasoning_content', or None if failed
    """
    try:
        # Build kwargs for acompletion
        kwargs = {
            "model": model,
            "messages": messages,
            "timeout": timeout
        }

        # Add reasoning_effort if specified
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort

        response = await acompletion(**kwargs)

        message = response.choices[0].message

        result = {
            'content': message.content,
        }

        # Include reasoning_content if present (standardized across providers)
        if hasattr(message, 'reasoning_content') and message.reasoning_content:
            result['reasoning_content'] = message.reasoning_content

        # Include thinking_blocks for Anthropic models
        if hasattr(message, 'thinking_blocks') and message.thinking_blocks:
            result['thinking_blocks'] = message.thinking_blocks

        return result

    except openai.AuthenticationError as e:
        print(f"Authentication error for {model}: {e}")
        return None
    except openai.RateLimitError as e:
        print(f"Rate limit error for {model}: {e}")
        return None
    except openai.APITimeoutError as e:
        print(f"Timeout error for {model}: {e}")
        return None
    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    reasoning_effort: Optional[str] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of LiteLLM model identifiers
        messages: List of message dicts to send to each model
        reasoning_effort: Reasoning effort level for all models

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    # Create tasks for all models
    tasks = [query_model(model, messages, reasoning_effort=reasoning_effort) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
