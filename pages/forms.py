import time
from uuid import uuid4

from django import forms
from django.conf import settings
from django.core import signing


class PublicSubmissionForm(forms.Form):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'}),
    )
    submission_token = forms.CharField(max_length=512, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['submission_token'] = self.new_submission_token()

    def new_submission_token(self):
        return signing.dumps(
            {'nonce': uuid4().hex, 'issued_at': time.time()},
            salt=f'pages.{self.submission_scope}',
        )

    def refresh_submission_token(self):
        data = self.data.copy()
        data['submission_token'] = self.new_submission_token()
        self.data = data

    def clean_submission_token(self):
        token = self.cleaned_data['submission_token']
        try:
            data = signing.loads(
                token, salt=f'pages.{self.submission_scope}',
                max_age=settings.PUBLIC_FORM_MAX_SECONDS,
            )
        except signing.BadSignature:
            raise forms.ValidationError('This form has expired. Please submit it again.')
        if time.time() - data['issued_at'] < settings.PUBLIC_FORM_MIN_SECONDS:
            raise forms.ValidationError('Please wait a couple of seconds and submit again.')
        return token

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Invalid submission.')
        return ''

    def clean_name(self):
        name = self.cleaned_data['name']
        if '\r' in name or '\n' in name:
            raise forms.ValidationError('Please enter your name on one line.')
        return name


class ContactForm(PublicSubmissionForm):
    submission_scope = 'contact'
    SERVICE_CHOICES = [
        ('courses', 'Courses'),
        ('learn', 'Learning Sessions'),
        ('performance', 'Live Performances'),
        ('record', 'Recording Sessions'),
        ('production', 'Music Production'),
        ('mixing', 'Mixing and Mastering'),
        ('booking', 'Event and Music Booking'),
        ('other', 'Other'),
    ]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Name', 'autocomplete': 'name'}),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'autocomplete': 'email'}),
    )
    services = forms.ChoiceField(choices=SERVICE_CHOICES)
    message = forms.CharField(
        min_length=10,
        max_length=3000,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type Your Message:'}),
    )


class CheckoutForm(PublicSubmissionForm):
    submission_scope = 'checkout'
    name = forms.CharField(max_length=120)
    email = forms.EmailField(max_length=254)
    notes = forms.CharField(max_length=2000, required=False)
