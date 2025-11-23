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

# Reasoning configuration
# reasoning_effort values: "none", "low", "medium", "high"
# LiteLLM translates this to provider-specific params (thinking_budget, thinking_level, etc.)
DEFAULT_REASONING_EFFORT = "high"  # Default for council models
CHAIRMAN_REASONING_EFFORT = "high"  # Default for chairman model
