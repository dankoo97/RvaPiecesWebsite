from django import template

register = template.Library()


@register.filter
def get_val(dictionary, key):
    return dictionary.get(key)


@register.filter
def sorted_keys(dictionary):
    return sorted(dictionary.keys())
