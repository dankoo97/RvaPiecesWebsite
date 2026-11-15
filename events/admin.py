import logging

from django.contrib import admin, messages
from django.shortcuts import redirect

from events.models import Event, Announcement, LichessStudy

logger = logging.getLogger(__name__)


# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    ready_only_fields = [
        "slug",
        "is_published",
        "published_version",
        "published_at",
        "archived_at",
    ]
    list_filter = ("is_published", "is_archived")
    actions = ["publish_draft", "archive_event"]

    fieldsets = (
        (
            "Content",
            {
                "fields": (
                    "name",
                    "short_description",
                    "long_description",
                    "location",
                    "calendar",
                )
            },
        ),
        ("Images", {"fields": ("icon", "image")}),
        ("Editorial", {"fields": ("is_promoted",)}),
        (
            "Chessnut",
            {"fields": ("chessnut_events", "chessnut_handler")},
        ),
        (
            "Discord Integration",
            {"fields": ("discord_channel_id", "discord_webhook_urls")},
        ),
        (
            "Tournament",
            {
                "classes": ("collapse",),
                "fields": (
                    "tournament_event_link",
                    "tournament_pairings_link",
                    "tournament_standings_link",
                ),
            },
        ),
    )

    @admin.action(description="Publish selected events")
    def publish_draft(self, request, queryset):
        for event in queryset.filter(is_published=False):
            try:
                event.publish()
            except Exception as e:
                logger.exception("Failed to publish event %s", event.pk)
                self.message_user(
                    request, f"Failed to publish {event}: {e}", messages.ERROR
                )
            else:
                self.message_user(request, f"Published {event}")

    @admin.action(description="Archive selected events")
    def archive_event(self, request, queryset):
        for event in queryset.filter(is_archived=False):
            event.archive()
            self.message_user(request, f"Archived {event}")

    def get_readonly_fields(self, request, obj=None):
        # Disable editing of published events
        if obj and (obj.is_published or obj.is_archived):
            editable_fields = (
                [
                    "is_promoted",
                ]
                if obj.is_published
                else []
            )
            return [
                f.name for f in self.model._meta.fields if f.name not in editable_fields
            ]
        return super().get_readonly_fields(request, obj)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)

        if obj and not obj.is_published:
            extra_context["show_save_and_publish"] = True

        if obj and obj.is_published:
            extra_context["show_archive"] = True

        if obj and obj.is_archived:
            extra_context["show_save"] = False
            extra_context["show_save_and_continue"] = False
            extra_context["show_save_and_add_another"] = False

        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        if "_publish" in request.POST:
            try:
                published_event = obj.publish()
            except Exception as e:
                logger.exception("Failed to publish event %s", obj.pk)
                self.message_user(
                    request, f"Failed to publish {obj}: {e}", messages.ERROR
                )
                return redirect(request.path)
            self.message_user(request, f"Published {obj}")
            return redirect(published_event.get_absolute_url())
        if "_archive" in request.POST:
            obj.archive()
            self.message_user(request, f"Archived {obj}")
            return redirect("admin:events_event_changelist")
        return super().response_change(request, obj)


admin.site.register(Announcement)
admin.site.register(LichessStudy)
