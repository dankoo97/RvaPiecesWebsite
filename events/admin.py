from django.contrib import admin

from events.models import Event, Announcement


# Register your models here.
class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Event, EventAdmin)
admin.site.register(Announcement)
