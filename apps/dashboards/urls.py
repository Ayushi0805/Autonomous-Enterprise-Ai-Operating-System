from django.urls import path

from .views import approve_request, dashboard_home, ingest_asset, report_detail, start_workflow, trigger_n8n_report, upload_asset

urlpatterns = [
    path("", dashboard_home, name="dashboard-home"),
    path("assets/upload/", upload_asset, name="dashboard-upload-asset"),
    path("assets/<int:asset_id>/ingest/", ingest_asset, name="dashboard-ingest-asset"),
    path("workflows/start/", start_workflow, name="dashboard-start-workflow"),
    path("workflows/<int:workflow_id>/trigger-report/", trigger_n8n_report, name="dashboard-trigger-n8n-report"),
    path("reports/<int:workflow_id>/", report_detail, name="dashboard-report-detail"),
    path("approvals/<int:approval_id>/<str:decision>/", approve_request, name="dashboard-approval-decision"),
]
