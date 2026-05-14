from typing import Any, TypedDict


class EnterpriseAIState(TypedDict, total=False):
    user_query: str
    workflow_type: str
    documents: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    eda_results: dict[str, Any]
    ml_results: dict[str, Any]
    lora_results: dict[str, Any]
    nlp_results: dict[str, Any]
    vision_results: dict[str, Any]
    plan: list[str]
    agent_outputs: list[dict[str, Any]]
    memory: dict[str, Any]
    approval_required: bool
    final_response: str
    ai_summary: dict[str, Any]
    crew_ai: dict[str, Any]
    orchestration_engine: str
    orchestration_warnings: list[str]
    errors: list[str]
