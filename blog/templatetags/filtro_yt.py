from django import template

register = template.Library()


@register.filter
def youtube_id(url):
    """Extrae el ID de video de una URL de YouTube."""
    if not url:
        return ''
    import re
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return ''