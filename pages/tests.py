from django.test import TestCase
from django.urls import reverse

class PagesTests(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_url_by_name(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_homepage_contains_correct_html(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Welcome to LLKMusic')
        self.assertContains(response, 'Contact Me')
        self.assertNotContains(response, 'Shopping Cart')
        self.assertNotContains(response, 'Add to Cart')

    def test_courses_page_status_code(self):
        response = self.client.get(reverse('courses'))
        self.assertEqual(response.status_code, 200)

    def test_courses_page_uses_correct_template(self):
        response = self.client.get(reverse('courses'))
        self.assertTemplateUsed(response, 'courses.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_courses_page_contains_cart(self):
        response = self.client.get(reverse('courses'))
        self.assertContains(response, 'LLKMusic Courses')
        self.assertContains(response, 'Shopping Cart')
        self.assertContains(response, 'Add to Cart')
