from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from typing import Callable, Sequence

from .agents import AGENT_REGISTRY
from .state import EnterpriseAIState


@dataclass(frozen=True)
class CrewAgentProfile:
    name: str
    role: str
    goal: str
    backstory: str


CREW_AGENT_PROFILES: dict[str, CrewAgentProfile] = {
    "retrieval": CrewAgentProfile(
        name="retrieval",
        role="Enterprise Knowledge Retrieval Agent",
        goal="Find the most relevant uploaded document chunks for the business question.",
        backstory="Specialist in document discovery and evidence collection across enterprise assets.",
    ),
    "rag": CrewAgentProfile(
        name="rag",
        role="Grounded Answer Agent",
        goal="Generate an evidence-backed answer using retrieved context and source citations.",
        backstory="RAG practitioner focused on keeping responses grounded in available documents.",
    ),
    "nlp": CrewAgentProfile(
        name="nlp",
        role="NLP Insight Agent",
        goal="Summarize text context, identify sentiment, and extract important keywords.",
        backstory="Language analyst that turns raw text into concise operational signals.",
    ),
    "vision": CrewAgentProfile(
        name="vision",
        role="Vision Intelligence Agent",
        goal="Analyze image assets for OCR, visual metadata, and useful multimodal findings.",
        backstory="Computer vision analyst for uploaded visual enterprise evidence.",
    ),
    "eda": CrewAgentProfile(
        name="eda",
        role="Exploratory Data Analysis Agent",
        goal="Profile datasets, produce statistical insights, and flag anomalies.",
        backstory="Data analyst focused on fast, practical understanding of tabular assets.",
    ),
    "ml_training": CrewAgentProfile(
        name="ml_training",
        role="AutoML Training Agent",
        goal="Train candidate ML models and summarize their usefulness for the workflow.",
        backstory="Machine learning engineer that benchmarks models against available datasets.",
    ),
    "lora_fine_tuning": CrewAgentProfile(
        name="lora_fine_tuning",
        role="LoRA Fine-Tuning Agent",
        goal="Train a PEFT LoRA adapter on uploaded text assets when adapter training is requested.",
        backstory="LLM adaptation specialist that creates lightweight domain adapters from enterprise text.",
    ),
    "reporting": CrewAgentProfile(
        name="reporting",
        role="Executive Reporting Agent",
        goal="Create a decision-ready AI report with summary, evidence, and next steps.",
        backstory="Business reporting specialist that converts agent outputs into stakeholder-ready reports.",
    ),
    "validation": CrewAgentProfile(
        name="validation",
        role="Validation and Governance Agent",
        goal="Check whether outputs are grounded and confidence is appropriate.",
        backstory="Governance reviewer for source presence, completion, and workflow quality.",
    ),
    "automation": CrewAgentProfile(
        name="automation",
        role="Workflow Automation Agent",
        goal="Queue downstream notifications and automation events when requested.",
        backstory="Operations automation agent for external workflow handoffs.",
    ),
}


class RegistryBackedCrew:
    """CrewAI-style crew that executes concrete agents from AGENT_REGISTRY."""

    def __init__(
        self,
        agent_names: Sequence[str],
        invoke_agent: Callable[[str, EnterpriseAIState], EnterpriseAIState],
    ) -> None:
        self.agent_names = [name for name in agent_names if name != "approval"]
        self.invoke_agent = invoke_agent

    def run(self, state: EnterpriseAIState) -> EnterpriseAIState:
        selected_agents = self._selected_agents()
        state["crew_ai"] = self.describe(selected_agents)
        for agent_name in selected_agents:
            state = self.invoke_agent(agent_name, state)
        return state

    def describe(self, selected_agents: Sequence[str] | None = None) -> dict:
        agents = list(selected_agents or self._selected_agents())
        return {
            "framework": "crewai",
            "execution_mode": "registry_backed",
            "crewai_package_available": self._crewai_package_available(),
            "agents": [asdict(self._profile_for(name)) for name in agents],
            "tasks": [
                {
                    "agent": name,
                    "description": self._task_description(name),
                    "expected_output": "Updated workflow state and agent execution log.",
                }
                for name in agents
            ],
        }

    def _selected_agents(self) -> list[str]:
        missing = [name for name in self.agent_names if name not in AGENT_REGISTRY]
        if missing:
            raise KeyError(f"Unknown crew agent(s): {', '.join(missing)}")
        return [name for name in self.agent_names if name in CREW_AGENT_PROFILES]

    def _profile_for(self, agent_name: str) -> CrewAgentProfile:
        return CREW_AGENT_PROFILES[agent_name]

    def _task_description(self, agent_name: str) -> str:
        profile = self._profile_for(agent_name)
        return f"{profile.goal} Use the existing AGENT_REGISTRY implementation named '{agent_name}'."

    def _crewai_package_available(self) -> bool:
        return importlib.util.find_spec("crewai") is not None
