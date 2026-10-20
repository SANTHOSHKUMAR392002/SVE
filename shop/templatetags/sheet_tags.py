from decimal import Decimal
from django import template
register = template.Library()

@register.filter
def trim(value):
    """2.500 -> 2.5, 10.000 -> 10 (no trailing zeros)."""
    if value is None or value == "": return value
    s = f"{Decimal(value):f}"
    return s.rstrip("0").rstrip(".") if "." in s else s
