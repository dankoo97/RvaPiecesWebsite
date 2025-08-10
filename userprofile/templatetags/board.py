from userprofile.models import BoardManager
from django import template

register = template.Library()


@register.filter
def sort_board(board):
    def get_highest_office(user):
        val = len(BoardManager.custom_order_by_group)
        for group in user.groups.filter(name__in=BoardManager.custom_order_by_group):
            val = min(val, BoardManager.custom_order_by_group.index(group.name))
        return val

    return sorted(board, key=lambda userprofile: get_highest_office(userprofile.user))
