# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- Contains `COUNCIL_MODELS` (list of LiteLLM model identifiers with provider prefixes)
- Contains `CHAIRMAN_MODEL` (model that synthesizes final answer)
- Contains `DEFAULT_REASONING_EFFORT` (default: "high") for council models
- Contains `CHAIRMAN_REASONING_EFFORT` (default: "high") for chairman
- Uses environment variables for API keys (see `.env.example`)
- Backend runs on **port 8001** (NOT 8000 - user had another app on 8000)

**`llm_client.py`**
- Uses LiteLLM for multi-provider support
- `query_model()`: Single async model query via `litellm.acompletion()`
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_content'
- Supports `reasoning_effort` parameter ("none", "low", "medium", "high")
- LiteLLM auto-translates to provider-specific params (thinking_budget, thinking_level, etc.)
- Graceful degradation: returns None on failure, continues with successful responses
- Supports any LLM provider: OpenAI, Anthropic, Google, Mistral, OpenRouter, etc.

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models
  - Accepts optional `reasoning_effort` parameter
  - Returns responses with optional `reasoning_content`
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
  - Uses `CHAIRMAN_REASONING_EFFORT` by default
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations
- `run_full_council()`: Orchestrates all stages, passes `reasoning_effort` through

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage, only returned via API

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- POST `/api/conversations/{id}/message` returns metadata in addition to stages
  - Accepts optional `reasoning_effort` in request body
- POST `/api/conversations/{id}/message/stream` for SSE streaming
  - Also accepts `reasoning_effort` parameter
- Metadata includes: label_to_model mapping and aggregate_rankings

### Frontend Structure (`frontend/src/`)

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Important: metadata is stored in the UI state for display but not persisted to backend JSON

**`components/ChatInterface.jsx`**
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- User messages wrapped in markdown-content class for padding

**`components/Stage1.jsx`**
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**
- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count
- Explanatory text clarifies that boldface model names are for readability only

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background (#f0fff0) to highlight conclusion

**Styling (`*.css`)**
- Light mode theme (not dark mode)
- Primary color: #4a90e2 (blue)
- Global markdown styling in `index.css` with `.markdown-content` class
- 12px padding on all markdown content to prevent cluttered appearance

## Key Design Decisions

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

This strict format allows reliable parsing while still getting thoughtful evaluations.

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-5.1", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs
- This builds trust and allows debugging of edge cases

## Important Implementation Details

### LiteLLM Model Naming
Models use LiteLLM provider prefixes to route to the correct API:
- `openai/gpt-5.1` - direct OpenAI
- `anthropic/claude-3-5-sonnet-20241022` - direct Anthropic
- `gemini/gemini-3-pro-preview` - direct Google
- `openrouter/meta-llama/llama-3-70b-instruct` - via OpenRouter

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for all supported providers.

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Docker: 8173 (nginx proxy)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration
Models are hardcoded in `backend/config.py` using LiteLLM provider prefixes. Chairman can be same or different from council members. The current default is Gemini as chairman per user preference.

### Reasoning Configuration
Reasoning/thinking is enabled by default at "high" effort level. LiteLLM's `reasoning_effort` parameter supports:
- `"none"` - Disable reasoning (significant cost savings, up to 96% cheaper)
- `"low"` - Minimal reasoning
- `"medium"` - Moderate reasoning
- `"high"` - Maximum reasoning (default)

LiteLLM auto-translates to provider-specific params:
- Anthropic → `thinking.budget_tokens`
- Gemini 2.5 Flash → `thinking_budget`
- Gemini 3+ → `thinking_level`

**Provider caveats:**
- Gemini 2.5 Pro cannot disable thinking
- Some models may not support all effort levels

API usage:
```json
POST /api/conversations/{id}/message
{
    "content": "Your question",
    "reasoning_effort": "medium"
}
```

### API Keys
Set API keys in `.env` (see `.env.example` for all supported providers):
- `OPENAI_API_KEY` - for OpenAI models
- `ANTHROPIC_API_KEY` - for Anthropic models
- `GEMINI_API_KEY` - for Google Gemini models
- `OPENROUTER_API_KEY` - for OpenRouter models

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses
5. **Docker Rebuilds**: Run `docker compose build` after changing dependencies (pyproject.toml, package.json)
6. **Docker Data Persistence**: Conversations persist in `llm-council-data` volume, survives container rebuilds

## Future Enhancement Ideas

- Configurable council/chairman via UI instead of config file
- Streaming responses instead of batch loading
- Export conversations to markdown/PDF
- Model performance analytics over time
- Custom ranking criteria (not just accuracy/insight)
- Frontend UI controls for reasoning effort selection
- Display reasoning_content in response tabs when present

## Latest Model Versions by Provider

Reference for the most current model identifiers (updated November 2025):

### OpenAI
- `openai/gpt-5.1`

### Google Gemini

- `gemini/gemini-2.5-flash`
- `gemini/gemini-2.5-flash-lite`
- `gemini/gemini-2.5-pro`
- `gemini/gemini-3.0-pro-preview`

### Anthropic
- `anthropic/claude-4.5-sonnet`

### xAI
- `xai/grok-4-1-fast-reasoning`

## Testing Notes

Use `test_openrouter.py` to verify API connectivity and test different model identifiers before adding to council. The script tests both streaming and non-streaming modes.

## Data Flow Summary

```
User Query + optional reasoning_effort
    ↓
Stage 1: Parallel queries (with reasoning) → [responses + reasoning_content]
    ↓
Stage 2: Anonymize → Parallel ranking queries (with reasoning) → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context (with reasoning)
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.
