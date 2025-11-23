"""LiteLLM client for making LLM requests to any provider."""

import asyncio
from typing import List, Dict, Any, Optional
from litellm import acompletion
import openai


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via LiteLLM.

    Args:
        model: LiteLLM model identifier with provider prefix
               (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    try:
        response = await acompletion(
            model=model,
            messages=messages,
            timeout=timeout
        )

        message = response.choices[0].message

        return {
            'content': message.content,
            'reasoning_details': getattr(message, 'reasoning_details', None)
        }

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
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of LiteLLM model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
