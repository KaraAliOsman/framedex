from django.urls import path
from projects.thermal_views import ThermalCatalogView, ThermalReviewView

from catalogs import views
from catalogs.glass_views import GlassPreviewView, GlassRulesView, GlassVariantView
from catalogs.reference_views import ReferenceSeriesView
from catalogs.series_views import (
    FamilyTemplatesView, SeriesCellsView, SeriesConfirmView, SeriesCreateView,
    SeriesHistoryView, SeriesSheetView,
)

urlpatterns = [
    path("family-templates/", FamilyTemplatesView.as_view(), name="catalog-family-templates"),
    path("series/", SeriesCreateView.as_view(), name="catalog-series-create"),
    path("series/<uuid:system_id>/", SeriesSheetView.as_view(), name="catalog-series-sheet"),
    path("series/<uuid:system_id>/cells/", SeriesCellsView.as_view(), name="catalog-series-cells"),
    path("series/<uuid:system_id>/confirm/", SeriesConfirmView.as_view(), name="catalog-series-confirm"),
    path("series/<uuid:system_id>/history/", SeriesHistoryView.as_view(), name="catalog-series-history"),
    path("systems/<uuid:system_id>/thermal/", ThermalCatalogView.as_view()),
    path("systems/<uuid:system_id>/thermal/<uuid:report_id>/review/", ThermalReviewView.as_view()),
    path("glass/preview/", GlassPreviewView.as_view(), name="catalog-glass-preview"),
    path("glass/rules/", GlassRulesView.as_view(), name="catalog-glass-rules"),
    path("glass/variants/", GlassVariantView.as_view(), name="catalog-glass-variants"),
    path("references/", ReferenceSeriesView.as_view(), name="catalog-reference-series"),
    path("systems/", views.SystemCollectionView.as_view(), name="catalog-system-list"),
    path(
        "systems/<uuid:row_id>/",
        views.SystemDetailView.as_view(),
        name="catalog-system-detail",
    ),
    path(
        "systems/<uuid:row_id>/review/",
        views.SystemReviewView.as_view(),
        name="catalog-system-review",
    ),
    path(
        "process-profiles/",
        views.ProcessProfileCollectionView.as_view(),
        name="catalog-process-profiles",
    ),
    path(
        "section-imports/",
        views.SectionImportCollectionView.as_view(),
        name="catalog-section-imports",
    ),
    path(
        "systems/<uuid:row_id>/workspace/",
        views.SystemWorkspaceView.as_view(),
        name="catalog-system-workspace",
    ),
    path("articles/", views.ArticleCollectionView.as_view(), name="catalog-article-list"),
    path(
        "articles/<uuid:row_id>/",
        views.ArticleDetailView.as_view(),
        name="catalog-article-detail",
    ),
    path(
        "articles/<uuid:row_id>/review/",
        views.ArticleReviewView.as_view(),
        name="catalog-article-review",
    ),
    path("glazing/", views.BeadCollectionView.as_view(), name="catalog-bead-list"),
    path(
        "glazing/<uuid:row_id>/",
        views.BeadDetailView.as_view(),
        name="catalog-bead-detail",
    ),
    path(
        "glazing/<uuid:row_id>/review/",
        views.BeadReviewView.as_view(),
        name="catalog-bead-review",
    ),
    path("hardware-kits/", views.KitCollectionView.as_view(), name="catalog-kit-list"),
    path(
        "hardware-kits/<uuid:row_id>/",
        views.KitDetailView.as_view(),
        name="catalog-kit-detail",
    ),
    path(
        "hardware-kits/<uuid:row_id>/review/",
        views.KitReviewView.as_view(),
        name="catalog-kit-review",
    ),
    path("evidence/", views.EvidenceCollectionView.as_view(), name="catalog-evidence-list"),
    path(
        "evidence/<uuid:row_id>/review/",
        views.EvidenceReviewView.as_view(),
        name="catalog-evidence-review",
    ),
]
