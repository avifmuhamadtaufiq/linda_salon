from __future__ import annotations

from typing import Any

from django import template

register = template.Library()


@register.filter(name="rupiah")
def rupiah(value: Any) -> str:
    if value is None or value == "":
        return "Rp 0"
    try:
        numeric_value = int(float(str(value)))
        if numeric_value < 0:
            return f"-Rp {abs(numeric_value):,}".replace(",", ".")
        return f"Rp {numeric_value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"
