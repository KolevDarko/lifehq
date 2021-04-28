from django import template

register = template.Library()


@register.filter('duration_format')
def hour_min_duration_format(value):
    value = int(value)
    hours = int(value / 60)
    minutes = value % 60
    if hours > 0:
        return '{}h {}m'.format(hours, minutes)
    elif minutes == 0:
        return ""
    else:
        return "{}m".format(minutes)
