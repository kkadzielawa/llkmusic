from django import forms


class ContactForm(forms.Form):
    SERVICE_CHOICES = [
        ('courses', 'Courses'),
        ('learn', 'Learning Sessions'),
        ('record', 'Recording Sessions'),
        ('other', 'Other'),
    ]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Name'}),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
    )
    services = forms.ChoiceField(choices=SERVICE_CHOICES)
    message = forms.CharField(
        min_length=10,
        max_length=3000,
        widget=forms.Textarea(attrs={'rows': 7, 'placeholder': 'Type Your Message:'}),
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            raise forms.ValidationError('Invalid submission.')
        return website
