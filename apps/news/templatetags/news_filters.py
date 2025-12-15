"""
Custom template filters for news app.
"""
import re
from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def strip_html(value):
    """Remove all HTML tags from text."""
    if not value:
        return ''
    return strip_tags(value)


@register.filter
def clean_html(value):
    """Remove HTML tags and clean up whitespace."""
    if not value:
        return ''
    # Strip HTML tags
    text = strip_tags(value)
    # Clean up multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

