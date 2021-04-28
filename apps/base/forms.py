import account.forms
from account.models import EmailAddress
from django import forms
from django.conf import settings
from sphinx.locale import _

class SignupForm(forms.Form):

    name = forms.CharField(
        label=_("Name"),
        max_length=30,
        widget=forms.TextInput(),
        required=True
    )
    password = account.forms.PasswordField(
        label=_("Password"),
        strip=settings.ACCOUNT_PASSWORD_STRIP,
    )
    password_confirm = account.forms.PasswordField(
        label=_("Password (again)"),
        strip=settings.ACCOUNT_PASSWORD_STRIP,
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.TextInput(), required=True)

    code = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.HiddenInput()
    )
    agree_terms = forms.BooleanField(required=True, error_messages={'required':
                                                                    'You must agree to our Terms of service to sign up.'})

    def clean_username(self):
        return self.cleaned_data["username"]

    def clean_email(self):
        value = self.cleaned_data["email"]
        qs = EmailAddress.objects.filter(email__iexact=value)
        if not qs.exists() or not settings.ACCOUNT_EMAIL_UNIQUE:
            return value
        raise forms.ValidationError(_("A user is registered with this email address."))

    def clean(self):
        if "password" in self.cleaned_data and "password_confirm" in self.cleaned_data:
            if self.cleaned_data["password"] != self.cleaned_data["password_confirm"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data

class ProjectResourceForm(forms.Form):
    the_file = forms.FileField()
