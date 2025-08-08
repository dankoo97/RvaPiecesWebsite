from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


# Create your models here.


class UserProfile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    bio = CKEditor5Field(blank=True)
    coaching_description = CKEditor5Field(blank=True)

    discord = models.CharField(max_length=50, blank=True)
    chess_com = models.CharField(max_length=50, blank=True)
    lichess = models.CharField(max_length=50, blank=True)
    other_links = models.JSONField(blank=True)

    image = models.ImageField(upload_to="media/images/profile_images/", blank=True)
    order = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
