from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post

class BlogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.post = Post.objects.create(
            title='My Blues Improvisation',
            slug='my-blues-improvisation',
            author=self.user,
            body='Some body text about blues guitar techniques.',
            published=True
        )
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=self.user,
            body='Draft body text.',
            published=False
        )

    def test_post_model_str(self):
        self.assertEqual(str(self.post), 'My Blues Improvisation')

    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Blues Improvisation')
        self.assertNotContains(response, 'Draft Post')
        self.assertTemplateUsed(response, 'blog/post_list.html')

    @patch('blog.views.connection.introspection.table_names', return_value=[])
    def test_post_list_view_handles_missing_table(self, mocked_table_names):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No blog posts found yet. Check back soon!')

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Blues Improvisation')
        self.assertContains(response, 'Some body text about blues guitar techniques.')
        self.assertTemplateUsed(response, 'blog/post_detail.html')

    @patch('blog.views.connection.introspection.table_names', return_value=[])
    def test_post_detail_view_handles_missing_table(self, mocked_table_names):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 404)

    def test_draft_post_detail_view_not_found(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.draft_post.slug]))
        self.assertEqual(response.status_code, 404)
