from django.urls import URLPattern, path

from authentication.views import AuthMeView

urlpatterns: list[URLPattern] = [
    path("me/", AuthMeView.as_view(), name="auth-me"),
]
