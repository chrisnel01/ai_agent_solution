from __future__ import annotations
import json
import os
import uuid
import re
import requests
import logging
from typing import Any, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"), 
     format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

logger = logging.getLogger("order_agent")

API_BASE = os.environ["DUMMY_API_BASE"].rstrip("/")
ORDERS_ENDPOINT = f"{API_BASE}/orders"
ORDER_ID_ENDPOINT = f"{API_BASE}/order"
ORDER_ID_RE = re.compile(
    r"(?:order|number|no\.?|#)\s*#?\s*(\d+)",
    re.IGNORECASE,
)
LIMIT_RE = re.compile(
    r"\b(?:first|top|limit|show|give|list|return)\D{0,10}(\d{1,3})\b",
    re.IGNORECASE,
)

SYSTEM_PROMPT = """
                You extract relevant order records from an unstructured order dataset.

                The user may ask a question in any format.

                Examples:
                - "Find Chris's order."
                - "Show me orders with a keyboard."
                - "Which purchases were over $50?"
                - "Only show Sarah's orders."
                - "What about the cheaper ones?"

                Rules:
                - Interpret the latest user request using the recent conversation.
                - Return only records relevant to the user's request.
                - Return only the amount of records that the user requests. Do not return more or less.
                - Use only facts supported by the raw source.
                - Never invent values.
                - Return an empty records list if nothing matches.
                - Normalize each result to the required schema.
                - Return totals as numeric values.
                - Return purchased items as a list of strings.
"""

class ParsedData(BaseModel):
    orderId: str | None = Field(
        default=None,
        description="Order ID found in the raw source.",
    )

    buyer: str | None = Field(
        default=None,
        description="Normalized buyer name.",
    )

    total: float | None = Field(
        default=None,
        description="Order total represented as a numeric value.",
    )

    items: list[str] = Field(
        default_factory=list,
        description="Purchased items represented as a list of strings.",
    )


class ExtractedOrders(BaseModel):
    records: list[ParsedData] = Field(default_factory=list)

class InputState(TypedDict):
    messages: list[BaseMessage]


class OutputState(TypedDict):
    messages: list[BaseMessage]
    records: list[dict[str, Any]]


class AgentState(MessagesState, total=False):
    cleaned_data: str
    records: list[dict[str, Any]]
    errors: list[str]

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "openai/gpt-oss-120b:exacto"),
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url=os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1"),
    temperature=0,
)

structured_llm = llm.with_structured_output(ExtractedOrders)

def get_latest_human_message(state: AgentState) -> HumanMessage:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message
    raise ValueError("The workflow requires at least one HumanMessage.")


def find_order_id(text: str) -> str | None:
    m = ORDER_ID_RE.search(text)
    return m.group(1) if m else None

def find_requested_limit(text: str) -> int | None:
    m = LIMIT_RE.search(text)
    return int(m.group(1)) if m else None

def fetch_raw_data_and_clean(state: AgentState) -> dict[str, Any]:
    message = get_latest_human_message(state).content
    order_id = find_order_id(message)

    if order_id:
        url = f"{ORDER_ID_ENDPOINT}/{order_id}"
        params = None
    else:
        url = ORDERS_ENDPOINT
        limit = find_requested_limit(message)
        params = {"limit": limit} if limit is not None else None

    logger.info("Fetching order data")

    try:
        response = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json, text/plain;q=0.9"},
            timeout=10,
        )
        response.raise_for_status()
        raw = response.text
    except Exception as e:
        logger.exception("Failed to retrive orders from API: %s", e)
        return {"cleaned_data": []}
    
    logger.info("Fetched order data")
    return {"cleaned_data": " ".join(raw.split())}

def extract_records(state: AgentState) -> dict[str, Any]:
    message = get_latest_human_message(state).content

    logger.info("Extracting records with LLM")

    try:
        result = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"USER REQUEST: {message}\n\nDATA:\n{state['cleaned_data']}"),
        ])
    except Exception as e:
        logger.exception("LLM extraction failed with: %s", e)
    records = [r.model_dump() for r in result.records]

    logger.info("LLM extraction complete")
    
    return {"records": [r.model_dump() for r in result.records]}


def finalize_records(state: AgentState) -> dict[str, Any]:
    records = state.get("records", [])
    response_payload = {"records": records}

    return {
        "records": records,
        "messages": [
            AIMessage(content=json.dumps(response_payload, indent=2))
        ],
    }



builder = StateGraph(
    AgentState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node("fetch_raw_data_and_clean", fetch_raw_data_and_clean)
builder.add_node("extract_records", extract_records)
builder.add_node("finalize_records", finalize_records)

builder.add_edge(START, "fetch_raw_data_and_clean")
builder.add_edge("fetch_raw_data_and_clean", "extract_records")
builder.add_edge("extract_records", "finalize_records")
builder.add_edge("finalize_records", END)

memory = InMemorySaver()

graph = builder.compile(checkpointer=memory)

def run_agent(user_text: str, config: dict) -> str:
    result = graph.invoke({"messages": [HumanMessage(content=user_text)]},
                          config
    )
    return result["messages"][-1].content
