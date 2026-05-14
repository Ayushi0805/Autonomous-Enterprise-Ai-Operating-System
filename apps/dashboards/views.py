from __future__ import annotations

import json
from urllib import request as urlrequest

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.approvals.models import ApprovalRequest
from apps.rag.services import RAGService
from apps.workflows.models import UploadedAsset, WorkflowRun
from apps.workflows.tasks import execute_workflow_run
from apps.workflows.utils import infer_asset_type


def dashboard_home(request):
    workflows = assets = approvals = []
    if request.user.is_authenticated:
        workflows = WorkflowRun.objects.filter(user=request.user).prefetch_related("logs").order_by("-created_at")[:10]
        assets = UploadedAsset.objects.filter(user=request.user).order_by("-created_at")[:10]
        approvals = ApprovalRequest.objects.filter(user=request.user).order_by("-created_at")[:10]
    return render(
        request,
        "dashboard/home.html",
        {
            "workflows": workflows,
            "assets": assets,
            "approvals": approvals,
            "n8n_configured": bool(getattr(settings, "N8N_WORKFLOW_COMPLETED_WEBHOOK_URL", "")),
        },
    )


@login_required(login_url="/admin/login/")
def upload_asset(request):
    if request.method != "POST":
        return redirect("dashboard-home")
    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, "Choose a file before uploading.")
        return redirect("dashboard-home")
    asset = UploadedAsset.objects.create(
        user=request.user,
        file=uploaded,
        name=uploaded.name,
        asset_type=infer_asset_type(uploaded.name),
    )
    messages.success(request, f"Uploaded {asset.name}. Asset ID: {asset.id}.")
    return redirect("dashboard-home")


@login_required(login_url="/admin/login/")
def start_workflow(request):
    if request.method != "POST":
        return redirect("dashboard-home")
    title = request.POST.get("title", "").strip() or "Untitled AI workflow"
    query = request.POST.get("query", "").strip()
    asset_ids = [int(value) for value in request.POST.getlist("asset_ids") if value.isdigit()]
    require_approval = request.POST.get("require_approval") == "on"
    workflow = WorkflowRun.objects.create(
        user=request.user,
        title=title,
        query=query,
        state={"approval_required": require_approval},
    )
    workflow.assets.set(UploadedAsset.objects.filter(user=request.user, id__in=asset_ids))
    execute_workflow_run.delay(workflow.id)
    workflow.refresh_from_db()
    messages.success(request, f"Started workflow #{workflow.id}: {workflow.status}.")
    return redirect("dashboard-home")


@login_required(login_url="/admin/login/")
def trigger_n8n_report(request, workflow_id):
    workflow = get_object_or_404(WorkflowRun, user=request.user, id=workflow_id)
    email = request.POST.get("email", "").strip() or request.user.email
    webhook_url = getattr(settings, "N8N_WORKFLOW_COMPLETED_WEBHOOK_URL", "")
    if not webhook_url:
        messages.error(request, "N8N_WORKFLOW_COMPLETED_WEBHOOK_URL is not configured.")
        return redirect("dashboard-home")
    payload = {
        "username": request.user.get_username(),
        "password": request.POST.get("password", ""),
        "workflow_id": workflow.id,
        "report_type": workflow.workflow_type or "enterprise_ai_report",
        "user_email": email,
    }
    try:
        _post_json(webhook_url, payload)
    except Exception as exc:
        messages.error(request, f"Could not trigger n8n report flow: {exc}")
    else:
        messages.success(request, f"Triggered n8n report flow for workflow #{workflow.id}.")
    return redirect("dashboard-home")


@login_required(login_url="/admin/login/")
def approve_request(request, approval_id, decision):
    approval = get_object_or_404(ApprovalRequest, user=request.user, id=approval_id)
    if decision not in {ApprovalRequest.Status.APPROVED, ApprovalRequest.Status.REJECTED}:
        messages.error(request, "Invalid approval decision.")
        return redirect("dashboard-home")
    approval.status = decision
    approval.decision_note = request.POST.get("note", "Decision submitted from dashboard.")
    approval.decided_at = timezone.now()
    approval.save(update_fields=["status", "decision_note", "decided_at"])
    approval.workflow.status = WorkflowRun.Status.COMPLETED if decision == ApprovalRequest.Status.APPROVED else WorkflowRun.Status.FAILED
    approval.workflow.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Approval #{approval.id} marked {decision}.")
    return redirect("dashboard-home")


@login_required(login_url="/admin/login/")
def ingest_asset(request, asset_id):
    asset = get_object_or_404(UploadedAsset, user=request.user, id=asset_id)
    docs = [{"id": asset.id, "name": asset.name, "path": asset.file.path, "asset_type": asset.asset_type}]
    result = RAGService().ingest(docs)
    messages.success(request, f"Indexed {asset.name}: {result['chunk_count']} chunks.")
    return redirect("dashboard-home")


@login_required(login_url="/admin/login/")
def report_detail(request, workflow_id):
    workflow = get_object_or_404(
        WorkflowRun.objects.prefetch_related("logs", "assets"),
        user=request.user,
        id=workflow_id,
    )
    state = workflow.state or {}
    logs = list(workflow.logs.all())
    anomalies = _extract_report_anomalies(state)
    dashboard = {
        "agent_count": len(logs),
        "average_confidence": round(sum(log.confidence for log in logs) / len(logs), 3) if logs else 0,
        "total_latency_ms": sum(log.latency_ms for log in logs),
        "has_anomalies": bool(anomalies),
        "workflow_type": workflow.workflow_type,
        "errors": state.get("errors", []),
    }
    return render(
        request,
        "dashboard/report_detail.html",
        {"workflow": workflow, "state": state, "logs": logs, "anomalies": anomalies, "dashboard": dashboard},
    )


def _extract_report_anomalies(state):
    anomalies = []
    for error in state.get("errors", []):
        anomalies.append({"severity": "critical", "type": "workflow_error", "message": error})
    for item in (state.get("eda_results") or {}).get("anomalies", []):
        anomalies.append({"severity": "high", "type": "eda_anomaly", "message": item})
    accuracy = ((state.get("ml_results") or {}).get("metrics") or {}).get("accuracy")
    if accuracy is not None and accuracy < 0.7:
        anomalies.append({"severity": "medium", "type": "model_accuracy", "message": f"Model accuracy is below threshold: {accuracy}"})
    return anomalies


def _post_json(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlrequest.urlopen(req, timeout=15) as response:
        response.read()
