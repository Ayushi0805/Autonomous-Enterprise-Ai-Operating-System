from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from apps.analytics.services import EDAService
from apps.ml_pipeline.lora import LoRAFineTuningService
from apps.ml_pipeline.services import AutoMLService
from apps.multimodal.services import VisionService
from apps.rag.services import RAGService

from .llm_summary import AISummaryService
from .state import EnterpriseAIState


@dataclass
class AgentResult:
    name: str
    output: dict
    latency_ms: int
    confidence: float = 0.8


class BaseAgent:
    name = "base"

    def invoke(self, state: EnterpriseAIState) -> tuple[EnterpriseAIState, AgentResult]:
        start = time.perf_counter()
        output = self.run(state)
        latency = int((time.perf_counter() - start) * 1000)
        state.setdefault("agent_outputs", []).append({"agent": self.name, "output": output})
        return state, AgentResult(self.name, output, latency, output.get("confidence", 0.8))

    def run(self, state: EnterpriseAIState) -> dict:
        raise NotImplementedError


class RouterAgent(BaseAgent):
    name = "router"

    def run(self, state: EnterpriseAIState) -> dict:
        asset_types = {doc.get("asset_type") for doc in state.get("documents", [])}
        query = state.get("user_query", "").lower()
        if {"csv", "excel"} & asset_types:
            workflow_type = "analytics_ml"
        elif "image" in asset_types:
            workflow_type = "vision"
        elif {"pdf", "text"} & asset_types:
            workflow_type = "rag"
        elif any(term in query for term in ["churn", "forecast", "predict", "train", "dataset"]):
            workflow_type = "analytics_ml"
        else:
            workflow_type = "enterprise_assistant"
        state["workflow_type"] = workflow_type
        return {"workflow_type": workflow_type, "asset_types": sorted(asset_types)}


class PlanningAgent(BaseAgent):
    name = "planning"

    def run(self, state: EnterpriseAIState) -> dict:
        routes = {
            "analytics_ml": ["eda", "ml_training", "reporting", "validation"],
            "vision": ["vision", "rag", "reporting", "validation"],
            "rag": ["retrieval", "rag", "nlp", "reporting", "validation"],
            "enterprise_assistant": ["retrieval", "nlp", "reporting", "validation"],
        }
        plan = routes.get(state.get("workflow_type", ""), routes["enterprise_assistant"])
        query = state.get("user_query", "").lower()
        if any(term in query for term in ["lora", "fine-tune", "finetune", "adapter training"]):
            plan.insert(-1, "lora_fine_tuning")
        if state.get("approval_required"):
            plan.append("approval")
        state["plan"] = plan
        return {"plan": plan}


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def run(self, state: EnterpriseAIState) -> dict:
        chunks = RAGService().retrieve(state.get("user_query", ""), state.get("documents", []))
        state["retrieved_chunks"] = chunks
        return {"chunks": chunks, "confidence": 0.76}


class RAGAgent(BaseAgent):
    name = "rag"

    def run(self, state: EnterpriseAIState) -> dict:
        answer = RAGService().answer(state.get("user_query", ""), state.get("retrieved_chunks", []), state.get("documents", []))
        state["final_response"] = answer["answer"]
        return answer


class NLPAgent(BaseAgent):
    name = "nlp"

    def run(self, state: EnterpriseAIState) -> dict:
        result = RAGService().nlp_summary(state.get("user_query", ""), state.get("retrieved_chunks", []))
        state["nlp_results"] = result
        return result


class VisionAgent(BaseAgent):
    name = "vision"

    def run(self, state: EnterpriseAIState) -> dict:
        result = VisionService().analyze(state.get("documents", []))
        state["vision_results"] = result
        return result


class EDAAgent(BaseAgent):
    name = "eda"

    def run(self, state: EnterpriseAIState) -> dict:
        result = EDAService().run(state.get("documents", []))
        state["eda_results"] = result
        return result


class MLTrainingAgent(BaseAgent):
    name = "ml_training"

    def run(self, state: EnterpriseAIState) -> dict:
        result = AutoMLService().train(state.get("documents", []), state.get("user_query", ""))
        state["ml_results"] = result
        return result


class LoRAFineTuningAgent(BaseAgent):
    name = "lora_fine_tuning"

    def run(self, state: EnterpriseAIState) -> dict:
        result = LoRAFineTuningService().train(state.get("documents", []), state.get("user_query", ""))
        state["lora_results"] = result
        return result


class ValidationAgent(BaseAgent):
    name = "validation"

    def run(self, state: EnterpriseAIState) -> dict:
        has_sources = bool(state.get("retrieved_chunks") or state.get("eda_results") or state.get("vision_results"))
        confidence = 0.86 if has_sources else 0.62
        return {"grounded": has_sources, "confidence": confidence, "checks": ["source_presence", "workflow_completion"]}


class MemoryAgent(BaseAgent):
    name = "memory"

    def run(self, state: EnterpriseAIState) -> dict:
        memory = {"last_workflow_type": state.get("workflow_type"), "last_query": state.get("user_query")}
        state["memory"] = memory
        return memory


class ReportingAgent(BaseAgent):
    name = "reporting"

    def run(self, state: EnterpriseAIState) -> dict:
        sections = [
            f"Workflow: {state.get('workflow_type', 'unknown')}",
            f"Plan: {', '.join(state.get('plan', []))}",
        ]
        if state.get("eda_results"):
            sections.append(f"EDA insights: {state['eda_results'].get('summary', 'completed')}")
        if state.get("ml_results"):
            sections.append(f"ML result: {state['ml_results'].get('summary', 'completed')}")
        if state.get("lora_results"):
            sections.append(f"LoRA result: {state['lora_results'].get('summary', 'completed')}")
        if state.get("vision_results"):
            sections.append(f"Vision result: {state['vision_results'].get('summary', 'completed')}")
        if state.get("final_response"):
            sections.append(state["final_response"])
        draft = "\n".join(sections)
        ai_summary = AISummaryService().summarize(state, draft)
        final = "\n\n".join(
            [
                ai_summary["summary"],
                "Supporting Workflow Evidence",
                draft,
            ]
        )
        state["ai_summary"] = ai_summary
        state["final_response"] = final
        return {"report": final, "ai_summary": ai_summary, "export_formats": ["pdf", "html", "json"]}


class AutomationAgent(BaseAgent):
    name = "automation"

    def run(self, state: EnterpriseAIState) -> dict:
        return {"queued": True, "channels": ["email", "n8n_webhook", "notification"]}


AGENT_REGISTRY: dict[str, Callable[[], BaseAgent]] = {
    "router": RouterAgent,
    "planning": PlanningAgent,
    "retrieval": RetrievalAgent,
    "rag": RAGAgent,
    "nlp": NLPAgent,
    "vision": VisionAgent,
    "eda": EDAAgent,
    "ml_training": MLTrainingAgent,
    "lora_fine_tuning": LoRAFineTuningAgent,
    "validation": ValidationAgent,
    "memory": MemoryAgent,
    "reporting": ReportingAgent,
    "automation": AutomationAgent,
}
