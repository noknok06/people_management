# your_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''
