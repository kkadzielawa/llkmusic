import logging
import json
from json import JSONDecodeError

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.templatetags.static import static
from django.views import View
from django.views.generic import FormView, TemplateView

from .catalog import MAX_CART_QUANTITY
from .forms import CheckoutForm, ContactForm
from .models import Course, Order, OrderItem


logger = logging.getLogger(__name__)


class SEOContextMixin:
    page_title = 'LLKMusic by Konrad Kadzielawa | Blues & Jazz Chicago'
    page_description = (
        'LLKMusic by Konrad Kadzielawa shares blues and jazz guitar lessons, '
        'courses, blog posts, llkmusicvideos, and Chicago music services.'
    )
    page_keywords = (
        'LLKMusic, Konrad Kadzielawa, llkmusicvideos, LLKMusicVideos, '
        'blues & jazz Chicago, Chicago blues guitar, Chicago jazz guitar, '
        'guitar lessons Chicago, guitar courses, music blog'
    )
    og_type = 'website'
    robots_content = 'index, follow'

    def get_json_ld(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('page_title', self.page_title)
        context.setdefault('page_description', self.page_description)
        context.setdefault('page_keywords', self.page_keywords)
        context.setdefault('og_type', self.og_type)
        context.setdefault('robots_content', self.robots_content)
        json_ld = self.get_json_ld()
        if json_ld:
            context['json_ld'] = json.dumps(json_ld, cls=DjangoJSONEncoder)
        return context


class HomePageView(SEOContextMixin, FormView):
    template_name = 'home.html'
    form_class = ContactForm
    page_title = 'LLKMusic by Konrad Kadzielawa | Blues & Jazz Chicago'
    page_description = (
        'LLKMusic by Chicago musician Konrad Kadzielawa offers blues and jazz '
        'guitar lessons, courses, blog posts, llkmusicvideos, and music services.'
    )

    def get_json_ld(self):
        home_url = f'{settings.SITE_URL}{reverse("home")}'
        blog_url = f'{settings.SITE_URL}{reverse("blog:post_list")}'
        courses_url = f'{settings.SITE_URL}{reverse("courses")}'
        services_url = f'{settings.SITE_URL}{reverse("services")}'
        person_id = f'{home_url}#konrad-kadzielawa'
        organization_id = f'{home_url}#organization'
        return {
            '@context': 'https://schema.org',
            '@graph': [
                {
                    '@type': 'Person',
                    '@id': person_id,
                    'name': 'Konrad Kadzielawa',
                    'alternateName': ['kkadzielawa', 'LLKMusic', 'llkmusicvideos'],
                    'url': home_url,
                    'image': f'{settings.SITE_URL}{static("img/logo.jpg")}',
                    'jobTitle': 'Blues and jazz musician, guitarist, and music educator',
                    'homeLocation': {
                        '@type': 'Place',
                        'name': 'Chicago, Illinois',
                    },
                    'knowsAbout': [
                        'Blues guitar',
                        'Jazz guitar',
                        'Chicago blues',
                        'Improvisation',
                        'Ear training',
                        'Guitar lessons',
                    ],
                    'sameAs': [
                        'https://www.linkedin.com/in/konradkadzielawa/',
                        'https://www.youtube.com/@llkmusicvideos',
                        'https://twitter.com/kkadzielawa',
                        'https://www.instagram.com/konradkadzielawa/',
                    ],
                },
                {
                    '@type': 'Organization',
                    '@id': organization_id,
                    'name': 'LLKMusic',
                    'alternateName': ['LLK Music', 'llkmusic', 'LLKMusicVideos', 'llkmusicvideos'],
                    'description': self.page_description,
                    'url': home_url,
                    'logo': f'{settings.SITE_URL}{static("img/logo.jpg")}',
                    'founder': {'@id': person_id},
                    'areaServed': {
                        '@type': 'City',
                        'name': 'Chicago',
                    },
                    'sameAs': [
                        'https://www.youtube.com/@llkmusicvideos',
                        'https://www.instagram.com/konradkadzielawa/',
                        'https://www.linkedin.com/in/konradkadzielawa/',
                    ],
                },
                {
                    '@type': 'WebSite',
                    '@id': f'{home_url}#website',
                    'name': 'LLKMusic',
                    'alternateName': ['llkmusic', 'LLKMusicVideos', 'llkmusicvideos'],
                    'url': home_url,
                    'publisher': {'@id': organization_id},
                    'inLanguage': 'en-US',
                    'about': {'@id': person_id},
                },
                *[
                    {
                        '@type': 'SiteNavigationElement',
                        'name': name,
                        'url': url,
                    }
                    for name, url in [
                        ('Blog', blog_url),
                        ('Courses', courses_url),
                        ('Services', services_url),
                    ]
                ],
            ],
        }

    def get_success_url(self):
        return f'{reverse("home")}#contact'

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        service_label = dict(ContactForm.SERVICE_CHOICES)[cleaned_data['services']]
        email = EmailMessage(
            subject=f'LLKMusic contact form: {service_label}',
            body=(
                f'Name: {cleaned_data["name"]}\n'
                f'Email: {cleaned_data["email"]}\n'
                f'Interested in: {service_label}\n\n'
                f'Message:\n{cleaned_data["message"]}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.CONTACT_FORM_RECIPIENTS,
            reply_to=[cleaned_data['email']],
        )

        try:
            email.send(fail_silently=False)
        except Exception:
            logger.exception('Contact form email delivery failed')
            messages.error(
                self.request,
                'Sorry, your message could not be sent. Please try again later.',
            )
            return self.render_to_response(self.get_context_data(form=form))

        messages.success(self.request, 'Thanks for reaching out. Your message has been sent.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please fix the highlighted fields and try again.')
        return super().form_invalid(form)


class CoursesPageView(SEOContextMixin, TemplateView):
    template_name = 'courses.html'
    page_title = 'Blues and Jazz Guitar Courses | LLKMusic Chicago'
    page_description = (
        'Explore LLKMusic courses from Konrad Kadzielawa for blues guitar '
        'foundations, jazz chords, private lessons, improvisation, and practice.'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Course.objects.filter(is_available=True)
        return context

    def get_json_ld(self):
        courses_url = f'{settings.SITE_URL}{reverse("courses")}'
        products = Course.objects.filter(is_available=True)
        return {
            '@context': 'https://schema.org',
            '@type': 'OfferCatalog',
            'name': 'LLKMusic blues and jazz guitar courses',
            'url': courses_url,
            'description': self.page_description,
            'provider': {
                '@type': 'Person',
                'name': 'Konrad Kadzielawa',
                'url': settings.SITE_URL,
            },
            'itemListElement': [
                {
                    '@type': 'Offer',
                    'name': product.name,
                    'description': product.description,
                    'price': str(product.price),
                    'priceCurrency': 'USD',
                    'availability': 'https://schema.org/InStock',
                    'url': courses_url,
                }
                for product in products
            ],
        }


class CartPageView(SEOContextMixin, TemplateView):
    template_name = 'cart.html'
    page_title = 'Shopping Cart | LLKMusic'
    page_description = 'Review selected LLKMusic courses, song packs, and private lesson options.'
    robots_content = 'noindex, nofollow'


class CheckoutView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid checkout data.'}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({'error': 'Invalid checkout data.'}, status=400)

        form = CheckoutForm(payload.get('customer') or {})
        if not form.is_valid():
            return JsonResponse({'error': 'Please enter your name and a valid email.'}, status=400)

        try:
            order_items = self._build_order_items(payload.get('items') or [])
        except ValueError as error:
            return JsonResponse({'error': str(error)}, status=400)

        subtotal = sum(item['line_total'] for item in order_items)
        with transaction.atomic():
            order = Order.objects.create(
                customer_name=form.cleaned_data['name'],
                customer_email=form.cleaned_data['email'],
                notes=form.cleaned_data.get('notes', ''),
                subtotal=subtotal,
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product_id=item['product'].slug,
                    product_name=item['product'].name,
                    unit_price=item['product'].price,
                    quantity=item['quantity'],
                    line_total=item['line_total'],
                )
                for item in order_items
            ])

        self._send_order_notification(order)
        return JsonResponse({
            'subtotal': f'{order.subtotal:.2f}',
            'item_count': sum(item['quantity'] for item in order_items),
            'message': self._build_success_message(order_items),
        })

    def _build_order_items(self, raw_items):
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError('Your cart is empty.')

        quantities_by_product_id = {}
        for raw_item in raw_items:
            product_id = raw_item.get('id') if isinstance(raw_item, dict) else None
            if not product_id:
                raise ValueError('One of the cart items is no longer available.')

            try:
                quantity = int(raw_item.get('quantity', 0))
            except (TypeError, ValueError):
                raise ValueError('Cart quantities must be valid numbers.')

            if quantity < 1:
                raise ValueError(f'Cart quantities must be between 1 and {MAX_CART_QUANTITY}.')

            quantities_by_product_id[product_id] = quantities_by_product_id.get(product_id, 0) + quantity
            if quantities_by_product_id[product_id] > MAX_CART_QUANTITY:
                raise ValueError(f'Cart quantities must be between 1 and {MAX_CART_QUANTITY}.')

        products_by_slug = Course.objects.filter(
            slug__in=quantities_by_product_id.keys(),
            is_available=True,
        ).in_bulk(field_name='slug')

        order_items = []
        for product_id, quantity in quantities_by_product_id.items():
            product = products_by_slug.get(product_id)
            if not product:
                raise ValueError('One of the cart items is no longer available.')

            order_items.append({
                'product': product,
                'quantity': quantity,
                'line_total': product.price * quantity,
            })

        return order_items

    def _build_success_message(self, order_items):
        purchased_items = [
            (
                f'{item["quantity"]} x {item["product"].name}'
                if item['quantity'] > 1
                else item['product'].name
            )
            for item in order_items
        ]
        return (
            f'Thanks. Your order for {self._format_item_list(purchased_items)} '
            'was received, and I will follow up by email.'
        )

    def _format_item_list(self, items):
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f'{items[0]} and {items[1]}'
        return f'{", ".join(items[:-1])}, and {items[-1]}'

    def _send_order_notification(self, order):
        lines = [
            f'Order: {order.order_number}',
            f'Name: {order.customer_name}',
            f'Email: {order.customer_email}',
            f'Total: ${order.subtotal:.2f}',
            '',
            'Items:',
        ]
        for item in order.items.all():
            lines.append(
                f'- {item.product_name} x {item.quantity} '
                f'@ ${item.unit_price:.2f} = ${item.line_total:.2f}'
            )
        if order.notes:
            lines.extend(['', 'Notes:', order.notes])

        email = EmailMessage(
            subject=f'LLKMusic order: {order.customer_name}',
            body='\n'.join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=settings.CONTACT_FORM_RECIPIENTS,
            reply_to=[order.customer_email],
        )
        try:
            email.send(fail_silently=False)
        except Exception:
            logger.exception('Order notification email delivery failed')


class ServicesPageView(SEOContextMixin, TemplateView):
    template_name = 'services.html'
    page_title = 'Chicago Blues and Jazz Music Services | LLKMusic'
    page_description = (
        'Book LLKMusic and Konrad Kadzielawa in Chicago for blues and jazz-forward '
        'performances, recording sessions, production, private lessons, and coaching.'
    )

    def get_json_ld(self):
        services_url = f'{settings.SITE_URL}{reverse("services")}'
        return {
            '@context': 'https://schema.org',
            '@type': 'ProfessionalService',
            'name': 'LLKMusic',
            'alternateName': ['LLK Music', 'llkmusic', 'LLKMusicVideos', 'llkmusicvideos'],
            'url': services_url,
            'description': self.page_description,
            'areaServed': {
                '@type': 'City',
                'name': 'Chicago',
            },
            'founder': {
                '@type': 'Person',
                'name': 'Konrad Kadzielawa',
            },
            'sameAs': [
                'https://www.youtube.com/@llkmusicvideos',
                'https://www.instagram.com/konradkadzielawa/',
                'https://www.linkedin.com/in/konradkadzielawa/',
            ],
            'hasOfferCatalog': {
                '@type': 'OfferCatalog',
                'name': 'LLKMusic services',
                'itemListElement': [
                    {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': service_name}}
                    for service_name in [
                        'Cover band performances',
                        'Recording sessions',
                        'Music production',
                        'Mixing and mastering',
                        'Private lessons and coaching',
                        'Event and music booking',
                    ]
                ],
            },
        }
