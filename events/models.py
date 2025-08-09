from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, null=False, blank=False)
    short_description = models.TextField(max_length=500)
    long_description = CKEditor5Field(blank=True)
    location = models.CharField(max_length=100)

    icon = models.ImageField(upload_to="media/images/events/", blank=True)
    image = models.ImageField(upload_to="media/images/events/", blank=True)

    is_promoted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    tournament_event_link = models.URLField(blank=True)
    tournament_pairings_link = models.URLField(blank=True)
    tournament_standings_link = models.URLField(blank=True)

    def __str__(self):
        return self.name


class EventInstance(models.Model):
    parent_event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.parent_event.name} - {self.date}"
