import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from .forms import ContactForm


logger = logging.getLogger(__name__)


class HomePageView(FormView):
    template_name = 'home.html'
    form_class = ContactForm

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


class CoursesPageView(TemplateView):
    template_name = 'courses.html'


class CartPageView(TemplateView):
    template_name = 'cart.html'


class ServicesPageView(TemplateView):
    template_name = 'services.html'
