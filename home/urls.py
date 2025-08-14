from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("faq/", views.faq, name="faq"),
    # TODO: Get stripe payment link
    path("donate/", RedirectView.as_view(url="https://stripe.com"), name="donate"),
]
