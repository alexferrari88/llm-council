"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# Council members - list of model identifiers using LiteLLM provider prefixes
# Examples:
#   - "openai/gpt-5.1" - direct OpenAI
#   - "xai/grok-4-1-fast-reasoning" - direct XAI
#   - "gemini/gemini-3-pro-preview" - direct Google
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "gemini/gemini-3-pro-preview",
    "xai/grok-4-1-fast-reasoning",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "gemini/gemini-3-pro-preview"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
