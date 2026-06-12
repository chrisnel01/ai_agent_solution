from __future__ import annotations

import json
import os
import uuid
from typing import Any, Literal, TypedDict

import requests
from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import RetryPolicy
from pydantic import BaseModel, Field, field_validator


load_dotenv()

API_BASE = os.environ["DUMMY_API_BASE"].rstrip("/")
ORDERS_ENDPOINT = f"{API_BASE}/orders"

class ParsedData(BaseModel):
    """
    Stable structure for every extracted order.
    """

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

    missing_fields: list[str] = Field(
        default_factory=list,
        description="Important fields absent from the raw source.",
    )

    @field_validator("total")
    @classmethod
    def round_total(cls, value: float | None) -> float | None:
        return round(value, 2) if value is not None else None


class ExtractedOrders(BaseModel):
    """
    Always return a list, even when there are zero or one matching orders.
    """

    records: list[ParsedData] = Field(default_factory=list)

class InputState(TypedDict):
    messages: list[BaseMessage]


class OutputState(TypedDict):
    messages: list[BaseMessage]
    records: list[dict[str, Any]]
    needs_review: bool
    errors: list[str]


class AgentState(MessagesState, total=False):
    """
    MessagesState already includes a messages field with LangGraph's
    built-in add_messages reducer.
    """

    raw_data: str
    cleaned_data: str

    candidate: ExtractedOrders | None
    attempts: int

    records: list[dict[str, Any]]
    needs_review: bool
    errors: list[str]

llm = ChatGroq(
    model=os.environ["MODEL_NAME"],
    temperature=0,
)

structured_llm = llm.with_structured_output(
    ExtractedOrders,
    include_raw=True,
)

def get_latest_human_message(state: AgentState) -> HumanMessage:
    """
    Retrieve the newest HumanMessage from the conversation.
    """

    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message

    raise ValueError("The workflow requires at least one HumanMessage.")


def format_recent_conversation(
    messages: list[BaseMessage],
    limit: int = 8,
) -> str:
    """
    Include recent history so the model can interpret conversational
    follow-ups such as: 'Only show the ones over $50.'
    """

    recent_messages = messages[-limit:]

    formatted_messages: list[str] = []

    for message in recent_messages:
        if isinstance(message, HumanMessage):
            role = "USER"
        elif isinstance(message, AIMessage):
            role = "ASSISTANT"
        else:
            role = "SYSTEM"

        formatted_messages.append(f"{role}: {message.content}")

    return "\n\n".join(formatted_messages)

def fetch_raw_data(state: AgentState) -> dict[str, Any]:
    """
    Always retrieve the full unstructured payload from GET /orders.
    """

    response = requests.get(
        ORDERS_ENDPOINT,
        headers={
            "Accept": "application/json, text/plain;q=0.9",
        },
        timeout=10,
    )

    response.raise_for_status()

    return {
        "raw_data": response.text,
        "attempts": 0,
        "errors": [],
        "needs_review": False,
    }

def clean_input(state: AgentState) -> dict[str, Any]:
    raw_data = state["raw_data"]

    cleaned_data = " ".join(raw_data.split())

    return {
        "cleaned_data": cleaned_data,
    }

def extract_records(state: AgentState) -> dict[str, Any]:
    attempts = state.get("attempts", 0) + 1
    previous_errors = state.get("errors", [])

    latest_human_message = get_latest_human_message(state)

    recent_conversation = format_recent_conversation(
        state["messages"],
    )

    feedback = ""

    if previous_errors:
        feedback = f"""
A previous extraction failed schema validation for these reasons:
{previous_errors}

Correct those issues only when supported by the raw source.
Do not invent missing values.
"""

    response = structured_llm.invoke(
        [
            SystemMessage(
                content="""
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
- Use only facts supported by the raw source.
- Never invent values.
- Return an empty records list if nothing matches.
- Normalize each result to the required schema.
- Return totals as numeric values.
- Add important absent values to missing_fields.
- Return purchased items as a list of strings.
"""
            ),
            HumanMessage(
                content=f"""
{feedback}

RECENT CONVERSATION:
{recent_conversation}

LATEST USER REQUEST:
{latest_human_message.content}

RAW UNSTRUCTURED ORDER DATA:
{state["cleaned_data"]}
"""
            ),
        ]
    )

    parsing_error = response["parsing_error"]
    parsed = response["parsed"]

    if parsing_error is not None or parsed is None:
        return {
            "candidate": None,
            "attempts": attempts,
            "errors": [
                f"Schema parsing error: {parsing_error}"
            ],
        }

    return {
        "candidate": parsed,
        "attempts": attempts,
        "errors": [],
    }

def route_after_extract(
    state: AgentState,
) -> Literal["retry", "finish", "review"]:
    if not state.get("errors"):
        return "finish"

    if state.get("attempts", 0) < 3:
        return "retry"

    return "review"

def finalize_records(state: AgentState) -> dict[str, Any]:
    candidate = state.get("candidate")

    records = (
        [
            record.model_dump(mode="json")
            for record in candidate.records
        ]
        if candidate is not None
        else []
    )

    response_payload = {
        "records": records,
        "needs_review": False,
        "errors": [],
    }

    return {
        **response_payload,
        "messages": [
            AIMessage(
                content=json.dumps(
                    response_payload,
                    indent=2,
                )
            )
        ],
    }


def flag_for_review(state: AgentState) -> dict[str, Any]:
    candidate = state.get("candidate")

    records = (
        [
            record.model_dump(mode="json")
            for record in candidate.records
        ]
        if candidate is not None
        else []
    )

    errors = state.get("errors", ["Extraction failed"])

    response_payload = {
        "records": records,
        "needs_review": True,
        "errors": errors,
    }

    return {
        **response_payload,
        "messages": [
            AIMessage(
                content=json.dumps(
                    response_payload,
                    indent=2,
                )
            )
        ],
    }

builder = StateGraph(
    AgentState,
    input_schema=InputState,
    output_schema=OutputState,
)

builder.add_node(
    "fetch_raw_data",
    fetch_raw_data,
    retry_policy=RetryPolicy(max_attempts=3),
)

builder.add_node("clean_input", clean_input)
builder.add_node("extract_records", extract_records)
builder.add_node("finalize_records", finalize_records)
builder.add_node("flag_for_review", flag_for_review)

builder.add_edge(START, "fetch_raw_data")
builder.add_edge("fetch_raw_data", "clean_input")
builder.add_edge("clean_input", "extract_records")

builder.add_conditional_edges(
    "extract_records",
    route_after_extract,
    {
        "retry": "extract_records",
        "finish": "finalize_records",
        "review": "flag_for_review",
    },
)

builder.add_edge("finalize_records", END)
builder.add_edge("flag_for_review", END)

memory = InMemorySaver()

graph = builder.compile(
    checkpointer=memory,
)

def main() -> None:
    """
    Accept free-form user messages until the user exits.
    """

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print("Order extraction agent")
    print("Ask about orders in any format. Type 'exit' to stop.\n")

    while True:
        try:
            user_text = input("You: ").strip()

            if user_text.lower() in {"exit", "quit", "q"}:
                print("Agent: Goodbye.")
                break

            if not user_text:
                print("Agent: Please enter a message.\n")
                continue

            result = graph.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_text)
                    ]
                },
                config=config,
            )

            latest_response = result["messages"][-1]

            print("\nAgent:")
            print(latest_response.content)
            print()

        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            print(
                f"\nAgent: The /orders endpoint returned HTTP "
                f"status {status_code}.\n"
            )

        except requests.RequestException as exc:
            print(
                f"\nAgent: The /orders request failed: {exc}\n"
            )

        except KeyboardInterrupt:
            print("\n\nAgent: Goodbye.")
            break

        except Exception as exc:
            print(f"\nAgent: The workflow failed: {exc}\n")


if __name__ == "__main__":
    main()