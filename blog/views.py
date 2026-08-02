import json

from django.conf import settings
from django.db import OperationalError, connection
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.views.generic import ListView, DetailView
from .models import Post


def _safe_published_posts():
    """Return published posts, or an empty queryset if the table is missing."""
    try:
        if Post._meta.db_table not in connection.introspection.table_names():
            return Post.objects.none()
        return Post.objects.filter(published=True).select_related('author')
    except OperationalError:
        return Post.objects.none()


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        return _safe_published_posts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Blues and Jazz Music Blog | LLKMusic'
        context['page_description'] = (
            'Read LLKMusic posts by Konrad Kadzielawa about blues guitar, jazz '
            'harmony, improvisation, ear training, Chicago blues, piano, and videos.'
        )
        context['page_keywords'] = (
            'LLKMusic blog, Konrad Kadzielawa, llkmusicvideos, blues guitar blog, '
            'jazz guitar blog, Chicago blues, improvisation lessons, ear training'
        )
        context['json_ld'] = json.dumps(
            {
                '@context': 'https://schema.org',
                '@type': 'Blog',
                'name': 'LLKMusic Blog',
                'url': f'{settings.SITE_URL}{reverse("blog:post_list")}',
                'description': context['page_description'],
                'publisher': {
                    '@type': 'Organization',
                    'name': 'LLKMusic',
                    'alternateName': ['LLK Music', 'llkmusic', 'LLKMusicVideos', 'llkmusicvideos'],
                    'url': settings.SITE_URL,
                },
                'author': {
                    '@type': 'Person',
                    'name': 'Konrad Kadzielawa',
                    'url': settings.SITE_URL,
                },
            },
            cls=DjangoJSONEncoder,
        )
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return _safe_published_posts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        body_text = ' '.join(strip_tags(self.object.body or '').split())
        description = Truncator(body_text).chars(160, truncate='...')
        if not description:
            description = f'{self.object.title} from the LLKMusic blues and jazz blog.'
        article_url = f'{settings.SITE_URL}{self.object.get_absolute_url()}'
        author_name = self.object.get_author_display_name()

        context['page_title'] = f'{self.object.title} | LLKMusic Blog'
        context['page_description'] = description
        context['page_keywords'] = (
            'blues guitar, jazz guitar, Chicago blues, music lessons, improvisation, '
            'LLKMusic, Konrad Kadzielawa, llkmusicvideos'
        )
        context['og_type'] = 'article'
        if self.object.featured_image:
            context['og_image'] = f'{settings.SITE_URL}{self.object.featured_image.url}'
        context['json_ld'] = json.dumps(
            {
                '@context': 'https://schema.org',
                '@type': 'Article',
                'headline': self.object.title,
                'description': description,
                'datePublished': self.object.created_at.isoformat(),
                'dateModified': self.object.updated_at.isoformat(),
                'author': {
                    '@type': 'Person',
                    'name': author_name,
                    'url': settings.SITE_URL,
                },
                'publisher': {
                    '@type': 'Organization',
                    'name': 'LLKMusic',
                    'url': settings.SITE_URL,
                },
                'mainEntityOfPage': article_url,
                'url': article_url,
            },
            cls=DjangoJSONEncoder,
        )
        return context
