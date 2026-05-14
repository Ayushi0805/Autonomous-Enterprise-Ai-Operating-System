from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("", include("apps.dashboards.urls")),
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/users/", include("apps.users.urls")),
    path("api/agents/", include("apps.ai_agents.urls")),
    path("api/workflows/", include("apps.workflows.urls")),
    path("api/rag/", include("apps.rag.urls")),
    path("api/ml/", include("apps.ml_pipeline.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/automation/", include("apps.automation.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/memory/", include("apps.memory.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/multimodal/", include("apps.multimodal.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
