from django import template
from django.utils import formats
import datetime

register = template.Library()


@register.filter
def get_val(dictionary, key):
    return dictionary.get(key)


@register.filter
def sorted_keys(dictionary):
    return sorted(dictionary.keys())


@register.filter
def iso_date(value):
    if not value:
        return ""
    try:
        parsed_date = datetime.date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return value
    return formats.date_format(parsed_date, "l, F j, Y")


@register.filter
def get_chessnut_studies(studies, event_id):
    return [study for study in studies if str(study.chessnut_event_id) == str(event_id)]
