from urllib.parse import urlparse

from django.conf import settings
from django.contrib.sitemaps.views import sitemap as django_sitemap


def canonical_sitemap(request, *args, **kwargs):
    parsed_site_url = urlparse(settings.SITE_URL)
    if parsed_site_url.netloc:
        request.META['HTTP_HOST'] = parsed_site_url.netloc
        request.META['SERVER_NAME'] = parsed_site_url.hostname or parsed_site_url.netloc
        request.META['SERVER_PORT'] = '443' if parsed_site_url.scheme == 'https' else '80'
        request.META['HTTP_X_FORWARDED_PROTO'] = parsed_site_url.scheme

    return django_sitemap(request, *args, **kwargs)
