from django import template

register = template.Library()


@register.filter(name="mongo_id")
def mongo_id(value):
    """Expose MongoDB _id safely to Django templates.

    Django intentionally rejects template variables/attributes beginning with
    an underscore. MongoDB documents conventionally use ``_id``, so templates
    must access the identifier through this filter instead of ``obj._id``.
    """
    if value is None:
        return ""
    if isinstance(value, dict):
        value = value.get("_id", value.get("id", ""))
    else:
        value = getattr(value, "_id", getattr(value, "id", ""))
    return str(value) if value is not None else ""
