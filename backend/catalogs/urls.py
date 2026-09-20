from django.urls import path

from catalogs import views

urlpatterns = [
    path("systems/", views.SystemCollectionView.as_view(), name="catalog-system-list"),
    path(
        "systems/<uuid:row_id>/",
        views.SystemDetailView.as_view(),
        name="catalog-system-detail",
    ),
    path("articles/", views.ArticleCollectionView.as_view(), name="catalog-article-list"),
    path(
        "articles/<uuid:row_id>/",
        views.ArticleDetailView.as_view(),
        name="catalog-article-detail",
    ),
    path("glazing/", views.BeadCollectionView.as_view(), name="catalog-bead-list"),
    path(
        "glazing/<uuid:row_id>/",
        views.BeadDetailView.as_view(),
        name="catalog-bead-detail",
    ),
    path("hardware-kits/", views.KitCollectionView.as_view(), name="catalog-kit-list"),
    path(
        "hardware-kits/<uuid:row_id>/",
        views.KitDetailView.as_view(),
        name="catalog-kit-detail",
    ),
]
