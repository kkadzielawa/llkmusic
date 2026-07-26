from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    body = models.TextField()
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_author_display_name(self):
        full_name = self.author.get_full_name()
        if full_name:
            return full_name
        if self.author.username == 'kkadzielawa':
            return 'Konrad Kadzielawa'
        return self.author.username

    def get_body_excerpt(self, words=35):
        text = ' '.join(strip_tags(self.body or '').split())
        return Truncator(text).words(words)
