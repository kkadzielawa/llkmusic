from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
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

    def test_kkadzielawa_author_displays_full_name(self):
        konrad = User.objects.create_user(username='kkadzielawa', password='testpassword')
        post = Post.objects.create(
            title='Chicago Blues Notes',
            slug='chicago-blues-notes',
            author=konrad,
            body='A note about blues phrasing.',
            published=True,
        )

        response = self.client.get(reverse('blog:post_detail', args=[post.slug]))
        self.assertContains(response, 'By Konrad Kadzielawa')
        self.assertNotContains(response, 'By kkadzielawa')

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
        self.assertContains(response, '<title>My Blues Improvisation | LLKMusic Blog</title>', html=False)
        self.assertContains(response, 'property="og:type" content="article"', html=False)
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, '"@type": "Article"')
        self.assertTemplateUsed(response, 'blog/post_detail.html')

    def test_post_detail_renders_rich_body_html(self):
        self.post.body = (
            '<p>Listen closely.</p>'
            '<figure class="media-size-medium"><img src="/media/blog/editor/blues.jpg" alt="Blues guitar"></figure>'
            '<figure class="media-embed media-size-large"><iframe src="https://www.youtube.com/embed/example?rel=0" title="Lesson" referrerpolicy="strict-origin-when-cross-origin"></iframe></figure>'
            '<figure class="media-size-small"><audio controls src="/media/blog/editor/track.mp3"></audio></figure>'
        )
        self.post.save()

        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        self.assertContains(response, '<div class="blog-entry-content">', html=False)
        self.assertContains(response, '<figure class="media-size-medium"><img src="/media/blog/editor/blues.jpg" alt="Blues guitar"></figure>', html=False)
        self.assertContains(response, 'referrerpolicy="strict-origin-when-cross-origin"', html=False)
        self.assertContains(response, '<figure class="media-size-small"><audio controls src="/media/blog/editor/track.mp3"></audio></figure>', html=False)

    def test_staff_can_upload_editor_image(self):
        staff_user = User.objects.create_user(
            username='editor',
            password='testpassword',
            is_staff=True,
        )
        upload = SimpleUploadedFile(
            'lesson.gif',
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif',
        )

        self.client.force_login(staff_user)
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(reverse('blog_editor_image_upload'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertIn('/media/blog/editor/image/lesson-', response.json()['location'])

    def test_staff_can_upload_editor_audio(self):
        staff_user = User.objects.create_user(
            username='audioeditor',
            password='testpassword',
            is_staff=True,
        )
        upload = SimpleUploadedFile(
            'track.mp3',
            b'ID3\x03\x00\x00\x00\x00\x00\x21',
            content_type='audio/mpeg',
        )

        self.client.force_login(staff_user)
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(reverse('blog_editor_media_upload'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['type'], 'audio')
        self.assertIn('/media/blog/editor/audio/track-', response.json()['location'])

    @patch('blog.views.connection.introspection.table_names', return_value=[])
    def test_post_detail_view_handles_missing_table(self, mocked_table_names):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 404)

    def test_draft_post_detail_view_not_found(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.draft_post.slug]))
        self.assertEqual(response.status_code, 404)
