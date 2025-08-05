from django.views import generic

from .models import UserProfile


# Create your views here.


class UserProfileView(generic.DetailView):
    model = UserProfile
    template_name = "userprofiles/bio.html"
