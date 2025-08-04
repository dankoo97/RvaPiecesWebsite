from django.urls import path

from . import views

urlpatterns = [
    path("who-we-are/", views.who_we_are, name="who_we_are"),
    path("code-of-conduct/", views.code_of_conduct, name="code_of_conduct"),
    path("contact-us/", views.contact_us, name="contact_us")
]