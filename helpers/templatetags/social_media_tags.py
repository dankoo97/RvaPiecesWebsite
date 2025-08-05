from django import template

register = template.Library()


@register.simple_tag
def instagram_page():
    return "https://www.instagram.com/rvapieces/"


@register.simple_tag
def facebook_page():
    return "https://www.facebook.com/RVAPieces/"


@register.simple_tag
def venmo_page():
    return "https://account.venmo.com/u/RVAPieces"


@register.simple_tag
def discord_invite():
    return "https://discord.com/invite/4wcTB5JuPn"


@register.simple_tag
def email():
    return "rvapieces@gmail.com"


@register.simple_tag
def chessnut_page():
    return "https://chessnut.club/c/rvapieces"
