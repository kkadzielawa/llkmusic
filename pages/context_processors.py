from django.conf import settings
from django.templatetags.static import static


def site_metadata(request):
    site_url = settings.SITE_URL.rstrip('/')
    path = request.path or '/'

    return {
        'site_url': site_url,
        'canonical_url': f'{site_url}{path}',
        'default_og_image': f'{site_url}{static("img/logo.jpg")}',
    }
