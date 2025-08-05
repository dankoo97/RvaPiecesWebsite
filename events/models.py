from django.db import models
from django.utils.text import slugify


# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, null=False, blank=False)
    short_description = models.TextField(max_length=500)
    long_description = models.TextField(max_length=10_000, blank=True)
    location = models.CharField(max_length=100)

    icon = models.ImageField(upload_to='media/images/events/', blank=True)
    image = models.ImageField(upload_to='media/images/events/', blank=True)

    event_id = models.CharField(max_length=100, primary_key=True)
    is_promoted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    tournament_event_link = models.URLField(blank=True)
    tournament_pairings_link = models.URLField(blank=True)
    tournament_standings_link = models.URLField(blank=True)

    def __str__(self):
        return self.name

