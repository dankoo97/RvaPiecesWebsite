"""
URL configuration for RvaPiecesWebsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include


urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", include("home.urls")),
        path("about/", include("about.urls")),
        path("events/", include("events.urls")),
        path("coaching/", include("coaching.urls")),
        # Redirects based on old site paths
        path(
            "contact/", lambda request: redirect("/about/contact-us/", permanent=True)
        ),
        path(
            "who-we-are/",
            lambda request: redirect("/about/who-we-are/", permanent=True),
        ),
        path(
            "code-of-conduct/",
            lambda request: redirect("/about/code-of-conduct/", permanent=True),
        ),
        path(
            "schedule/", lambda request: redirect("/events/schedule/", permanent=True)
        ),
        path(
            "calendar/", lambda request: redirect("/events/schedule/", permanent=True)
        ),
        path(
            "private-coaching/",
            lambda request: redirect("/coaching/private-coaching/", permanent=True),
        ),
        path(
            "steven-jankowski-memorial/",
            lambda request: redirect("/events/schedule/", permanent=True),
        ),
        path("ckeditor5/", include("django_ckeditor_5.urls")),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
