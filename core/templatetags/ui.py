from django import template

register = template.Library()


@register.filter
def csv(value):
    """'Python, Django ,SQL' -> ['Python', 'Django', 'SQL']"""
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """Current query string with `page` replaced - keeps filters when paginating."""
    params = context["request"].GET.copy()
    params["page"] = page_number
    return "?" + params.urlencode()


@register.simple_tag(takes_context=True)
def has_filters(context):
    """True when the request carries any filter other than `page` / `sort`."""
    params = context["request"].GET
    return any(value for key, value in params.items() if key not in {"page", "sort"})
