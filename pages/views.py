import logging
import json

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.templatetags.static import static
from django.views.generic import FormView, TemplateView

from .forms import ContactForm


logger = logging.getLogger(__name__)


class SEOContextMixin:
    page_title = 'LLKMusic | Blues & Jazz Guitar Lessons, Blog & Courses'
    page_description = (
        'LLKMusic shares blues and jazz guitar lessons, courses, blog posts, '
        'and performance services from Chicago musician Konrad Kadzielawa.'
    )
    page_keywords = (
        'LLKMusic, blues guitar lessons, jazz guitar lessons, Chicago musician, '
        'guitar courses, music blog'
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
    page_title = 'LLKMusic | Blues & Jazz Guitar Lessons and Courses'
    page_description = (
        'Learn blues and jazz guitar with LLKMusic through blog lessons, '
        'downloadable courses, private coaching, and Chicago-based music services.'
    )

    def get_json_ld(self):
        home_url = self.request.build_absolute_uri(reverse('home'))
        person_id = f'{home_url}#konrad-kadzielawa'
        organization_id = f'{home_url}#organization'
        return {
            '@context': 'https://schema.org',
            '@graph': [
                {
                    '@type': 'Person',
                    '@id': person_id,
                    'name': 'Konrad Kadzielawa',
                    'url': home_url,
                    'image': self.request.build_absolute_uri(static('img/personal_photo.png')),
                    'jobTitle': 'Blues and jazz musician',
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
                    'url': home_url,
                    'logo': self.request.build_absolute_uri(static('img/logo.png')),
                    'founder': {'@id': person_id},
                },
                {
                    '@type': 'WebSite',
                    '@id': f'{home_url}#website',
                    'name': 'LLKMusic',
                    'url': home_url,
                    'publisher': {'@id': organization_id},
                },
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
    page_title = 'Blues and Jazz Guitar Courses | LLKMusic'
    page_description = (
        'Explore LLKMusic courses and song packs for blues guitar foundations, '
        'jazz chords, private lessons, improvisation, rhythm, and practice tracks.'
    )


class CartPageView(SEOContextMixin, TemplateView):
    template_name = 'cart.html'
    page_title = 'Shopping Cart | LLKMusic'
    page_description = 'Review selected LLKMusic courses, song packs, and private lesson options.'
    robots_content = 'noindex, nofollow'


class ServicesPageView(SEOContextMixin, TemplateView):
    template_name = 'services.html'
    page_title = 'Music Services, Lessons, and Booking | LLKMusic'
    page_description = (
        'Book LLKMusic for blues and jazz-forward performances, recording sessions, '
        'music production, mixing, mastering, private lessons, and coaching.'
    )
