# Order Agent

A small LangGraph agent with a simple PyQt UI. It fetches messy order text from a dummy customer API, then uses `openai/gpt-oss-120b:exacto` through OpenRouter with Pydantic structured output to return clean JSON records.

## Run

```bash
pip install -r requirements.txt

# .env
OPENROUTER_API_KEY=your-openrouter-api-key
MODEL_NAME=openai/gpt-oss-120b:exacto

python main.py
```

`main.py` starts the local dummy API and opens the desktop UI.

## Architecture

```
User
  |
  v
 Agent (agent.py)
  |
  +--> fetch_raw_data_and_clean
  |      |
  |      v
  |   Dummy Orders API (dummy_customer_api.py)
  |
  +--> extract_records
  |      |
  |      v
  |   OpenRouter LLM
  |
  v
finalize_records -> JSON response
```
