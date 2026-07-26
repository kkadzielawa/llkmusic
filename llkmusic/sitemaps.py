from django.contrib.sitemaps import Sitemap
from django.db import OperationalError, connection
from django.urls import reverse

from blog.models import Post


class StaticViewSitemap(Sitemap):
    protocol = 'https'

    def items(self):
        return [
            {'name': 'home', 'priority': 1.0, 'changefreq': 'weekly'},
            {'name': 'blog:post_list', 'priority': 0.9, 'changefreq': 'weekly'},
            {'name': 'courses', 'priority': 0.8, 'changefreq': 'monthly'},
            {'name': 'services', 'priority': 0.8, 'changefreq': 'monthly'},
        ]

    def location(self, item):
        return reverse(item['name'])

    def priority(self, item):
        return item['priority']

    def changefreq(self, item):
        return item['changefreq']


class BlogPostSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        try:
            if Post._meta.db_table not in connection.introspection.table_names():
                return Post.objects.none()
            return Post.objects.filter(published=True)
        except OperationalError:
            return Post.objects.none()

    def lastmod(self, obj):
        return obj.updated_at
