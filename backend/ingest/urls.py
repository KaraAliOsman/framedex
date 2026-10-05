from django.urls import path
from ingest import catalog_views

from ingest.views import (
    CatalogImportConfirmView,
    CatalogImportDetailView,
    CatalogImportsView,
    ProjectImportConfirmView,
    ProjectImportDetailView,
    ProjectImportsView,
)

urlpatterns = [
    path("catalog-imports/template/", catalog_views.CatalogTemplateView.as_view(), name="catalog-template"),
    path("catalog-imports/schema/", catalog_views.CatalogTemplateSchemaView.as_view(), name="catalog-template-schema"),
    path("catalog-imports/<uuid:import_id>/review/", catalog_views.CatalogImportReviewView.as_view(), name="catalog-import-review"),
    path("catalog-imports/<uuid:import_id>/publish/", catalog_views.CatalogImportPublishView.as_view(), name="catalog-import-publish"),
    path("catalog-imports/<uuid:import_id>/undo/", catalog_views.CatalogImportUndoView.as_view(), name="catalog-import-undo"),
    path("catalog-imports/<uuid:import_id>/export/", catalog_views.CatalogImportExportView.as_view(), name="catalog-import-export"),
    path(
        "projects/<uuid:project_id>/imports/",
        ProjectImportsView.as_view(),
        name="project-imports",
    ),
    path(
        "projects/<uuid:project_id>/imports/<uuid:import_id>/",
        ProjectImportDetailView.as_view(),
        name="project-import-detail",
    ),
    path(
        "projects/<uuid:project_id>/imports/<uuid:import_id>/confirm/",
        ProjectImportConfirmView.as_view(),
        name="project-import-confirm",
    ),
    path(
        "catalog-imports/",
        CatalogImportsView.as_view(),
        name="catalog-imports",
    ),
    path(
        "catalog-imports/<uuid:import_id>/",
        CatalogImportDetailView.as_view(),
        name="catalog-import-detail",
    ),
    path(
        "catalog-imports/<uuid:import_id>/confirm/",
        CatalogImportConfirmView.as_view(),
        name="catalog-import-confirm",
    ),
]
