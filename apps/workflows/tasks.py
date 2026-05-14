try:
    from aeaios.celery import app
except ModuleNotFoundError:
    class _LocalTask:
        def task(self, func):
            func.delay = func
            return func

    app = _LocalTask()


@app.task
def execute_workflow_run(workflow_id):
    from .models import WorkflowRun
    from apps.ai_agents.orchestrator import EnterpriseAIOrchestrator
    from apps.workflows.n8n import notify_workflow_completed

    workflow = WorkflowRun.objects.get(id=workflow_id)
    EnterpriseAIOrchestrator(workflow).run()
    workflow.refresh_from_db()
    notify_workflow_completed(workflow)
    return workflow.id
