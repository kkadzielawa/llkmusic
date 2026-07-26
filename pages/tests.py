from unittest.mock import patch
import json

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Course, Order


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

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('pages.views.logger.exception')
    @patch('pages.views.EmailMessage.send', side_effect=OSError('SMTP timeout'))
    def test_contact_form_email_failure_returns_error_message(self, mock_send, mock_logger_exception):
        response = self.client.post(reverse('home'), {
            'name': 'John Coltrane',
            'email': 'john@example.com',
            'services': 'record',
            'message': 'I would like to discuss a recording session soon.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry, your message could not be sent.')
        self.assertEqual(len(mail.outbox), 0)
        mock_send.assert_called_once_with(fail_silently=False)
        mock_logger_exception.assert_called_once_with('Contact form email delivery failed')

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
        self.assertContains(response, 'data-product-id="blues-foundations"')
        self.assertContains(response, 'data-product-id="jazz-chords"')
        self.assertContains(response, 'data-product-id="private-session"')
        self.assertNotContains(response, 'Shopping Cart')
        self.assertNotContains(response, 'cart-items')

    def test_courses_page_renders_available_admin_courses(self):
        Course.objects.create(
            slug='bebop-lines',
            name='Bebop Line Builder',
            category='Course',
            description='Build bebop language over common progressions.',
            price='59.00',
            display_order=5,
        )

        response = self.client.get(reverse('courses'))

        self.assertContains(response, 'Bebop Line Builder')
        self.assertContains(response, 'data-product-id="bebop-lines"')
        self.assertContains(response, 'data-product-price="59.00"')

    def test_courses_page_hides_unavailable_courses(self):
        Course.objects.create(
            slug='archived-course',
            name='Archived Course',
            category='Course',
            description='This should not be visible.',
            price='29.00',
            is_available=False,
        )

        response = self.client.get(reverse('courses'))

        self.assertNotContains(response, 'Archived Course')
        self.assertNotContains(response, 'data-product-id="archived-course"')

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
        self.assertContains(response, 'Submit Order')
        self.assertContains(response, reverse('cart_checkout'))
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


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='LLKMusic <sender@example.com>',
    CONTACT_FORM_RECIPIENTS=['orders@example.com'],
)
class CheckoutTests(TestCase):
    def test_valid_checkout_creates_order_and_sends_email(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Wes Montgomery',
                    'email': 'wes@example.com',
                    'notes': 'I prefer evenings.',
                },
                'items': [
                    {'id': 'blues-foundations', 'quantity': 2},
                    {'id': 'private-session', 'quantity': 1},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['subtotal'], '173.00')
        self.assertEqual(data['item_count'], 3)
        self.assertNotIn('order_number', data)
        self.assertIn('2 x Blues Guitar Foundations', data['message'])
        self.assertIn('Private Learning Session', data['message'])

        order = Order.objects.get()
        self.assertEqual(order.customer_name, 'Wes Montgomery')
        self.assertEqual(order.customer_email, 'wes@example.com')
        self.assertEqual(order.subtotal, 173)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['orders@example.com'])
        self.assertEqual(mail.outbox[0].reply_to, ['wes@example.com'])
        self.assertIn('Blues Guitar Foundations x 2', mail.outbox[0].body)

    def test_checkout_rejects_unknown_product(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Visitor',
                    'email': 'visitor@example.com',
                },
                'items': [
                    {'id': 'unknown-product', 'quantity': 1},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_checkout_rejects_missing_customer_email(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Visitor',
                    'email': 'not-an-email',
                },
                'items': [
                    {'id': 'jazz-chords', 'quantity': 1},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_merges_duplicate_products(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Grant Green',
                    'email': 'grant@example.com',
                },
                'items': [
                    {'id': 'jazz-chords', 'quantity': 1},
                    {'id': 'jazz-chords', 'quantity': 2},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, 105)
        item = order.items.get()
        self.assertEqual(item.product_id, 'jazz-chords')
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.line_total, 105)
        self.assertIn('3 x Jazz Chord Starter Pack', response.json()['message'])

    def test_checkout_accepts_admin_created_course(self):
        Course.objects.create(
            slug='solo-guitar',
            name='Solo Guitar Arranging',
            category='Course',
            description='Arrange melody, bass, and inner voices for solo guitar.',
            price='64.00',
        )

        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Emily Remler',
                    'email': 'emily@example.com',
                },
                'items': [
                    {'id': 'solo-guitar', 'quantity': 2},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('2 x Solo Guitar Arranging', response.json()['message'])
        order = Order.objects.get()
        self.assertEqual(order.subtotal, 128)
        self.assertEqual(order.items.get().product_name, 'Solo Guitar Arranging')

    def test_checkout_rejects_unavailable_course(self):
        Course.objects.create(
            slug='draft-course',
            name='Draft Course',
            category='Course',
            description='Not ready yet.',
            price='40.00',
            is_available=False,
        )

        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Visitor',
                    'email': 'visitor@example.com',
                },
                'items': [
                    {'id': 'draft-course', 'quantity': 1},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_duplicate_products_over_quantity_limit(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps({
                'customer': {
                    'name': 'Visitor',
                    'email': 'visitor@example.com',
                },
                'items': [
                    {'id': 'private-session', 'quantity': 20},
                    {'id': 'private-session', 'quantity': 1},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_invalid_json(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data='{',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_rejects_non_object_json(self):
        response = self.client.post(
            reverse('cart_checkout'),
            data=json.dumps([]),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)


@override_settings(SECURE_SSL_REDIRECT=False)
class SEOTests(TestCase):
    def test_homepage_has_search_metadata(self):
        response = self.client.get(reverse('home'))
        self.assertContains(
            response,
            '<title>LLKMusic | Blues &amp; Jazz Guitar Lessons and Courses</title>',
            html=False,
        )
        self.assertContains(response, 'name="description"', html=False)
        self.assertContains(response, 'property="og:site_name" content="LLKMusic"', html=False)
        self.assertContains(response, '<link rel="canonical" href="http://testserver/">', html=False)
        self.assertContains(response, 'application/ld+json')
        self.assertContains(response, '"@type": "WebSite"')

    def test_robots_txt_lists_sitemap(self):
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User-agent: *')
        self.assertContains(response, 'Sitemap:')
        self.assertContains(response, reverse('sitemap_xml'))

    def test_sitemap_contains_public_pages_and_excludes_cart(self):
        response = self.client.get(reverse('sitemap_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('home'))
        self.assertContains(response, reverse('blog:post_list'))
        self.assertContains(response, reverse('courses'))
        self.assertContains(response, reverse('services'))
        self.assertNotContains(response, reverse('cart'))

    def test_cart_page_is_noindex(self):
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'name="robots" content="noindex, nofollow"', html=False)
