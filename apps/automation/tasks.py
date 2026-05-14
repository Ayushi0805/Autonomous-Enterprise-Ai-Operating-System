try:
    from aeaios.celery import app
except ModuleNotFoundError:
    class _LocalTask:
        def task(self, func):
            func.delay = func
            return func

    app = _LocalTask()


@app.task
def trigger_automation(run_id):
    from .models import AutomationRun

    run = AutomationRun.objects.get(id=run_id)
    run.status = "completed"
    run.save(update_fields=["status"])
    return run.id
