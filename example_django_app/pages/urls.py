"""URL routes for the example home page."""

from django.urls import path

from pages.views import home

app_name = "pages"

urlpatterns = [
    path("", home, name="home"),
]
