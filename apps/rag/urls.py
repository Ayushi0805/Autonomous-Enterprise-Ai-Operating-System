from django.urls import path

from .views import DocumentIngestView, SemanticSearchView

urlpatterns = [
    path("ingest/", DocumentIngestView.as_view(), name="document-ingest"),
    path("search/", SemanticSearchView.as_view(), name="semantic-search"),
]
