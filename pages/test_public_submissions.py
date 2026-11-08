import json
import time
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.core import mail, signing
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Order, SubmissionGuard


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    CONTACT_FORM_RECIPIENTS=['owner@example.com'],
    TRUST_PROXY_IP=False,
)
class PublicSubmissionTests(TestCase):
    def token(self, scope='contact', age=5):
        with patch('django.core.signing.time.time', return_value=time.time() - age):
            return signing.dumps(
                {'nonce': uuid4().hex, 'issued_at': time.time()},
                salt=f'pages.{scope}',
            )

    def contact_data(self, **changes):
        return {
            'name': 'A Visitor', 'email': 'visitor@example.com',
            'services': 'learn', 'message': 'I would like to book a guitar lesson.',
            'submission_token': self.token(), **changes,
        }

    def checkout_data(self, **changes):
        return {
            'customer': {'name': 'A Visitor', 'email': 'visitor@example.com'},
            'items': [{'id': 'blues-foundations', 'quantity': 1}],
            'submission_token': self.token('checkout'), **changes,
        }

    def checkout(self, data=None, **extra):
        return self.client.post(
            reverse('cart_checkout'), json.dumps(data if data is not None else self.checkout_data()),
            content_type='application/json', **extra,
        )

    def test_valid_forms_send_only_to_owner(self):
        self.assertEqual(self.client.post(reverse('home'), self.contact_data()).status_code, 302)
        self.assertEqual(self.checkout().status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(all(message.to == ['owner@example.com'] for message in mail.outbox))

    @override_settings(PUBLIC_FORM_MIN_SECONDS=0)
    def test_rendered_forms_work_with_csrf_enforcement(self):
        client = Client(enforce_csrf_checks=True)
        home = client.get(reverse('home'))
        self.assertContains(home, 'name="submission_token"')
        data = self.contact_data(
            submission_token=home.context['form']['submission_token'].value(),
            csrfmiddlewaretoken=client.cookies['csrftoken'].value,
        )
        self.assertEqual(client.post(reverse('home'), data).status_code, 302)
        cart = client.get(reverse('cart'))
        self.assertContains(cart, 'name="submission_token"')
        response = client.post(
            reverse('cart_checkout'),
            json.dumps(self.checkout_data(
                submission_token=cart.context['checkout_form']['submission_token'].value(),
            )),
            content_type='application/json', HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    def test_missing_tokens_rejected_on_both_endpoints(self):
        response = self.client.post(reverse('home'), self.contact_data(submission_token=''))
        self.assertTrue(response.context['form'].has_error('submission_token'))
        self.assertEqual(self.checkout(self.checkout_data(submission_token='')).status_code, 400)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Order.objects.exists())

    def test_tampered_cross_form_expired_and_too_fast_tokens_rejected(self):
        tokens = [self.token() + 'changed', self.token('checkout'), self.token(age=86401), self.token(age=0)]
        for token in tokens:
            with self.subTest(token=token):
                response = self.client.post(reverse('home'), self.contact_data(submission_token=token))
                self.assertTrue(response.context['form'].has_error('submission_token'))
                self.assertNotEqual(response.context['form']['submission_token'].value(), token)
        self.assertEqual(len(mail.outbox), 0)

    def test_checkout_rejects_honeypot(self):
        response = self.checkout(self.checkout_data(website='https://spam.example'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_contact_replay_and_duplicate_with_new_token_send_once(self):
        data = self.contact_data()
        self.assertEqual(self.client.post(reverse('home'), data).status_code, 302)
        self.assertEqual(self.client.post(reverse('home'), data).status_code, 409)
        self.assertEqual(self.client.post(reverse('home'), self.contact_data()).status_code, 409)
        self.assertEqual(len(mail.outbox), 1)

    def test_reusing_token_for_different_message_is_rejected(self):
        data = self.contact_data()
        self.client.post(reverse('home'), data)
        data['message'] = 'A different message with the same used token.'
        self.assertEqual(self.client.post(reverse('home'), data).status_code, 409)
        self.assertEqual(len(mail.outbox), 1)

    def test_checkout_replay_and_new_token_duplicate_create_one_order(self):
        data = self.checkout_data()
        self.assertEqual(self.checkout(data).status_code, 200)
        self.assertEqual(self.checkout(data).status_code, 409)
        self.assertEqual(self.checkout().status_code, 409)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(PUBLIC_FORM_IP_LIMIT=2)
    def test_ip_limit_is_shared_by_contact_and_checkout_and_has_retry_after(self):
        self.client.post(reverse('home'), {})
        self.checkout({})
        response = self.checkout()
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response['Retry-After']), 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(PUBLIC_FORM_IP_LIMIT=1)
    def test_visitor_cannot_bypass_limit_by_spoofing_forwarded_headers(self):
        self.client.post(reverse('home'), {}, HTTP_X_FORWARDED_FOR='192.0.2.1')
        response = self.checkout(
            HTTP_X_FORWARDED_FOR='192.0.2.2', HTTP_X_REAL_IP='192.0.2.3',
        )
        self.assertEqual(response.status_code, 429)

    @override_settings(PUBLIC_FORM_IP_LIMIT=1, TRUST_PROXY_IP=True)
    def test_trusted_proxy_distinguishes_visitors_but_ignores_forwarded_for(self):
        self.client.post(reverse('home'), {}, HTTP_X_REAL_IP='192.0.2.1')
        self.assertEqual(self.checkout(HTTP_X_REAL_IP='192.0.2.2').status_code, 200)
        self.assertEqual(self.checkout(
            HTTP_X_REAL_IP='192.0.2.1', HTTP_X_FORWARDED_FOR='192.0.2.9',
        ).status_code, 429)

    @override_settings(PUBLIC_FORM_IP_LIMIT=1)
    def test_ipv6_privacy_address_rotation_does_not_bypass_limit(self):
        self.client.post(reverse('home'), {}, REMOTE_ADDR='2001:db8:1:2::1')
        self.assertEqual(self.checkout(REMOTE_ADDR='2001:db8:1:2::2').status_code, 429)

    @override_settings(PUBLIC_FORM_EMAIL_LIMIT=1)
    def test_email_limit_is_case_insensitive_and_shared_between_endpoints_and_ips(self):
        self.client.post(reverse('home'), self.contact_data(email='Visitor@EXAMPLE.com'))
        response = self.checkout(REMOTE_ADDR='192.0.2.1')
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response)
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(Order.objects.exists())

    @patch('pages.views.logger.exception')
    def test_smtp_failure_allows_genuine_retry(self, mock_logger):
        data = self.contact_data()
        with patch('pages.views.EmailMessage.send', side_effect=OSError('SMTP unavailable')):
            self.client.post(reverse('home'), data)
        self.assertEqual(self.client.post(reverse('home'), data).status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_expired_claims_are_removed_without_storing_personal_data(self):
        SubmissionGuard.objects.create(key='old', expires_at=timezone.now() - timedelta(seconds=1))
        self.client.post(reverse('home'), self.contact_data())
        self.assertFalse(SubmissionGuard.objects.filter(key='old').exists())
        for guard in SubmissionGuard.objects.all():
            self.assertRegex(guard.key, r'^[0-9a-f]{64}$')

    @override_settings(PUBLIC_FORM_IP_LIMIT=100)
    def test_malformed_checkout_values_return_errors_without_side_effects(self):
        invalid_payloads = [
            self.checkout_data(customer='not an object'),
            self.checkout_data(customer=['not', 'an', 'object']),
            self.checkout_data(items=[{'id': ['invalid'], 'quantity': 1}]),
            self.checkout_data(items=[{'id': {'invalid': True}, 'quantity': 1}]),
            self.checkout_data(items=[None]),
        ]
        invalid_payloads += [
            self.checkout_data(items=[{'id': 'blues-foundations', 'quantity': value}])
            for value in (True, 1.5, '2', 0, -1, 21, None, {}, [])
        ]
        for data in invalid_payloads:
            with self.subTest(data=data):
                self.assertEqual(self.checkout(data).status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_newlines_in_customer_name_cannot_reach_email_headers(self):
        response = self.checkout(self.checkout_data(customer={
            'name': 'Visitor\r\nBcc: victim@example.com', 'email': 'visitor@example.com',
        }))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_oversized_checkout_rejected(self):
        response = self.checkout(self.checkout_data(customer={'notes': 'x' * 70000}))
        self.assertEqual(response.status_code, 413)
        self.assertFalse(Order.objects.exists())

    def test_deeply_nested_json_rejected_without_server_error(self):
        response = self.client.post(
            reverse('cart_checkout'), '[' * 2000 + '0' + ']' * 2000,
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_rate_window_recovers_after_expiry(self):
        with override_settings(PUBLIC_FORM_IP_LIMIT=1):
            self.client.post(reverse('home'), {})
            self.assertEqual(self.checkout().status_code, 429)
            future = timezone.now() + timedelta(minutes=11)
            with patch('pages.abuse.timezone.now', return_value=future):
                self.assertEqual(self.checkout().status_code, 200)

    def test_csrf_is_still_required_on_both_endpoints(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('home'), self.contact_data()).status_code, 403)
        self.assertEqual(client.post(
            reverse('cart_checkout'), json.dumps(self.checkout_data()), content_type='application/json',
        ).status_code, 403)
        self.assertEqual(len(mail.outbox), 0)
