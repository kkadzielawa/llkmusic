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

    def test_courses_page_no_longer_shows_cart_panel(self):
        response = self.client.get(reverse('courses'))
        self.assertContains(response, 'LLKMusic Courses')
        self.assertContains(response, 'Add to Cart')
        self.assertNotContains(response, 'Shopping Cart')
        self.assertNotContains(response, 'cart-items')

    def test_cart_page_status_code(self):
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)

    def test_cart_page_uses_correct_template(self):
        response = self.client.get(reverse('cart'))
        self.assertTemplateUsed(response, 'cart.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_cart_page_contains_cart_only_copy(self):
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'Review your selected items')
        self.assertContains(response, 'Shopping Cart')
        self.assertNotContains(response, 'Add to Cart')

    def test_services_page_status_code(self):
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)

    def test_services_page_uses_correct_template(self):
        response = self.client.get(reverse('services'))
        self.assertTemplateUsed(response, 'services.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_services_page_contains_service_copy(self):
        response = self.client.get(reverse('services'))
        self.assertContains(response, 'Cover Band Performances')
        self.assertContains(response, 'Recording Sessions')
        self.assertContains(response, 'Mixing and Mastering')
