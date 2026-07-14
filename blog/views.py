from django.db import OperationalError, connection
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


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return _safe_published_posts()
