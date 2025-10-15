from django.urls import path
from django.views.generic import RedirectView

from RvaPiecesWebsite.settings import DONATION_LINK
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("faq/", views.faq, name="faq"),
    path("donate/", RedirectView.as_view(url=DONATION_LINK), name="donate"),
]
