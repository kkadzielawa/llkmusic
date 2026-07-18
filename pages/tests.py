from django.core import mail
from django.test import TestCase, override_settings
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
        self.assertContains(response, 'action="/#contact"')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="services"')
        self.assertContains(response, 'name="message"')
        self.assertNotContains(response, 'Shopping Cart')
        self.assertNotContains(response, 'Add to Cart')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='LLKMusic <sender@example.com>',
        CONTACT_FORM_RECIPIENTS=['kkadzi25@gmail.com'],
    )
    def test_contact_form_valid_submission_sends_email(self):
        response = self.client.post(reverse('home'), {
            'name': 'Miles Davis',
            'email': 'miles@example.com',
            'services': 'learn',
            'message': 'I would like to book a private lesson next month.',
        })

        self.assertRedirects(response, '/#contact', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['kkadzi25@gmail.com'])
        self.assertEqual(sent_email.reply_to, ['miles@example.com'])
        self.assertIn('Learning Sessions', sent_email.subject)
        self.assertIn('Miles Davis', sent_email.body)
        self.assertIn('miles@example.com', sent_email.body)
        self.assertIn('Learning Sessions', sent_email.body)
        self.assertIn('I would like to book a private lesson next month.', sent_email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_contact_form_invalid_submission_does_not_send_email(self):
        response = self.client.post(reverse('home'), {
            'name': '',
            'email': 'not-an-email',
            'services': 'learn',
            'message': 'short',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please fix the highlighted fields and try again.')
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_contact_form_honeypot_submission_does_not_send_email(self):
        response = self.client.post(reverse('home'), {
            'name': 'Spam Sender',
            'email': 'spam@example.com',
            'services': 'other',
            'message': 'This message has enough characters to pass validation.',
            'website': 'https://example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

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
