from django.urls import path

from .views import WorkflowReportPdfView, WorkflowReportView

urlpatterns = [
    path("<int:workflow_id>/", WorkflowReportView.as_view(), name="workflow-report"),
    path("<int:workflow_id>/pdf/", WorkflowReportPdfView.as_view(), name="workflow-report-pdf"),
]
