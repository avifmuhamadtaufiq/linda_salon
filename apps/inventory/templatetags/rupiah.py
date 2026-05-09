from django import template

register = template.Library()

@register.filter
def rupiah(value):
    """Format angka ke format Rupiah: Rp 1.000.000"""
    try:
        value = int(value)
        return f"Rp {value:,}".replace(',', '.')
    except (ValueError, TypeError):
        return value