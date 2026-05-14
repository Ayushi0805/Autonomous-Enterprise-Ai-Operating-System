from __future__ import annotations

from django.db import transaction

from apps.approvals.models import ApprovalRequest
from apps.workflows.models import AgentExecutionLog, WorkflowRun

from .agents import AGENT_REGISTRY
from .crew import RegistryBackedCrew
from .state import EnterpriseAIState


class EnterpriseAIOrchestrator:
    """Stateful agent runner; uses LangGraph when installed, with a deterministic fallback."""

    def __init__(self, workflow: WorkflowRun):
        self.workflow = workflow

    def run(self) -> EnterpriseAIState:
        self.workflow.status = WorkflowRun.Status.RUNNING
        self.workflow.save(update_fields=["status", "updated_at"])
        state = self._initial_state()
        try:
            state = self._run_agents(state)
            if state.get("approval_required"):
                ApprovalRequest.objects.get_or_create(
                    workflow=self.workflow,
                    defaults={"user": self.workflow.user, "title": f"Approve {self.workflow.title}", "payload": state},
                )
                self._persist(state, WorkflowRun.Status.WAITING_APPROVAL)
            else:
                self._persist(state, WorkflowRun.Status.COMPLETED)
        except Exception as exc:
            state.setdefault("errors", []).append(str(exc))
            self._persist(state, WorkflowRun.Status.FAILED)
        return state

    def _initial_state(self) -> EnterpriseAIState:
        return {
            "user_query": self.workflow.query,
            "workflow_type": self.workflow.workflow_type,
            "documents": [
                {"id": asset.id, "name": asset.name, "path": asset.file.path, "asset_type": asset.asset_type}
                for asset in self.workflow.assets.all()
            ],
            "retrieved_chunks": [],
            "agent_outputs": [],
            "approval_required": self.workflow.state.get("approval_required", False),
            "memory": {},
            "errors": [],
        }

    def _run_agents(self, state: EnterpriseAIState) -> EnterpriseAIState:
        try:
            return self._run_langgraph(state)
        except Exception as exc:
            state.setdefault("orchestration_warnings", []).append(f"LangGraph fallback used: {exc}")
            return self._run_deterministic(state)

    def _run_deterministic(self, state: EnterpriseAIState) -> EnterpriseAIState:
        for agent_name in ["router", "planning"]:
            state = self._invoke(agent_name, state)
        state = self._run_registry_crew(state)
        state = self._invoke("memory", state)
        return state

    def _run_langgraph(self, state: EnterpriseAIState) -> EnterpriseAIState:
        from langgraph.graph import END, StateGraph

        def router_node(current_state: EnterpriseAIState) -> EnterpriseAIState:
            current_state["orchestration_engine"] = "langgraph"
            return self._invoke("router", current_state)

        def planning_node(current_state: EnterpriseAIState) -> EnterpriseAIState:
            return self._invoke("planning", current_state)

        def plan_executor_node(current_state: EnterpriseAIState) -> EnterpriseAIState:
            return self._run_registry_crew(current_state)

        def memory_node(current_state: EnterpriseAIState) -> EnterpriseAIState:
            return self._invoke("memory", current_state)

        graph = StateGraph(EnterpriseAIState)
        graph.add_node("router", router_node)
        graph.add_node("planning", planning_node)
        graph.add_node("plan_executor", plan_executor_node)
        graph.add_node("memory", memory_node)
        graph.set_entry_point("router")
        graph.add_edge("router", "planning")
        graph.add_edge("planning", "plan_executor")
        graph.add_edge("plan_executor", "memory")
        graph.add_edge("memory", END)
        return graph.compile().invoke(state)

    def _run_registry_crew(self, state: EnterpriseAIState) -> EnterpriseAIState:
        crew = RegistryBackedCrew(state.get("plan", []), self._invoke)
        return crew.run(state)

    def _invoke(self, agent_name: str, state: EnterpriseAIState) -> EnterpriseAIState:
        agent = AGENT_REGISTRY[agent_name]()
        state, result = agent.invoke(state)
        AgentExecutionLog.objects.create(
            workflow=self.workflow,
            agent_name=result.name,
            input_snapshot={"workflow_type": state.get("workflow_type"), "plan": state.get("plan", [])},
            output=result.output,
            latency_ms=result.latency_ms,
            confidence=result.confidence,
        )
        return state

    @transaction.atomic
    def _persist(self, state: EnterpriseAIState, status: str) -> None:
        self.workflow.workflow_type = state.get("workflow_type", "")
        self.workflow.state = dict(state)
        self.workflow.final_response = state.get("final_response", "")
        self.workflow.status = status
        self.workflow.save(update_fields=["workflow_type", "state", "final_response", "status", "updated_at"])
