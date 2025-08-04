from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    event_url = models.URLField()
    icon = models.ImageField(upload_to='media/images/events/')

    def __str__(self):
        return self.location

