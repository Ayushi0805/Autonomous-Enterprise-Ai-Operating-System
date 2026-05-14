from __future__ import annotations

import json
import logging
from urllib import request

from django.conf import settings

logger = logging.getLogger(__name__)


def notify_workflow_completed(workflow) -> None:
    workflow_type = workflow.workflow_type or ""
    if workflow_type == "analytics_ml":
        webhook_url = getattr(settings, "N8N_ML_WEBHOOK_URL", "")
    elif workflow_type == "vision":
        webhook_url = getattr(settings, "N8N_VISION_WEBHOOK_URL", "")
    elif workflow_type == "rag":
        webhook_url = getattr(settings, "N8N_RAG_WEBHOOK_URL", "")
    else:
        webhook_url = getattr(settings, "N8N_WORKFLOW_COMPLETED_WEBHOOK_URL", "")

    if not webhook_url:
        return

    payload = {
        "workflow_id": workflow.id,
        "report_type": workflow.workflow_type or "enterprise_ai_report",
        "user_email": workflow.user.email,
        "status": workflow.status,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            response.read()
    except Exception as exc:
        logger.warning("Could not notify n8n workflow webhook: %s", exc)
