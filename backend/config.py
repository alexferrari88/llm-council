"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# Council members - list of model identifiers using LiteLLM provider prefixes
# Examples:
#   - "openai/gpt-4o" - direct OpenAI
#   - "anthropic/claude-3-5-sonnet-20241022" - direct Anthropic
#   - "gemini/gemini-1.5-pro" - direct Google
#   - "openrouter/openai/gpt-4o" - via OpenRouter
COUNCIL_MODELS = [
    "openai/gpt-4o",
    "gemini/gemini-1.5-pro",
    "anthropic/claude-3-5-sonnet-20241022",
    "openrouter/x-ai/grok-2",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "gemini/gemini-1.5-pro"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
