from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django_registration import validators

from hackathon_site.utils import is_registration_open
from registration.models import Application, Team, User
from registration.widgets import MaterialFileInput


class SignUpForm(UserCreationForm):
    """
    Form for registering a new user account.

    Similar to django_registration's ``RegistrationForm``, but doesn't
    require a username field. Instead, email is a required field, and
    username is automatically set to be the email. This is ultimately
    simpler than creating a custom user model to use email as username.
    """

    error_css_class = "invalid"

    class Meta(UserCreationForm.Meta):
        fields = [
            User.get_email_field_name(),
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]
        labels = {
            User.get_email_field_name(): _("Email"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "password1": _("Password"),
            "password2": _("Confirm Password"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_field = User.get_email_field_name()
        self.fields[email_field].validators.extend(
            (
                validators.HTML5EmailValidator(),
                validators.validate_confusables_email,
                validators.CaseInsensitiveUnique(
                    User, email_field, "This email is unavailable"
                ),
            )
        )
        self.label_suffix = ""

        # This overrides the default labels set by UserCreationForm
        for field, label in self._meta.labels.items():
            self.fields[field].label = label

        for field in self._meta.fields:
            self.fields[field].required = True

    def save(self, commit=True):
        """
        Set the user's username to their email when saving

        This is much simpler than the alternative of creating a
        custom user model without a username field, but a caveat
        nonetheless.
        """

        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ApplicationForm(forms.ModelForm):
    error_css_class = "invalid"

    class Meta:
        model = Application
        fields = [
            "birthday",
            "gender",
            "ethnicity",
            "school",
            "study_level",
            "graduation_year",
            "resume",
            "resume_sharing",
            "eligibility_agree",
            "conduct_agree",
            "data_agree",
        ]
        widgets = {
            "birthday": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "school": forms.Select(
                # Choices will be populated by select2
                attrs={"class": "select2-school-select"},
                choices=((None, ""),),
            ),
            "resume": MaterialFileInput(),
            "graduation_year": forms.NumberInput(attrs={"placeholder": 2020}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        self.fields["conduct_agree"].required = True
        self.fields["data_agree"].required = True
        self.fields["eligibility_agree"].required = True

    def clean(self):
        if not is_registration_open():
            raise forms.ValidationError(
                _("Registration has closed."), code="registration_closed"
            )

        cleaned_data = super().clean()
        if hasattr(self.user, "application"):
            raise forms.ValidationError(
                _("User has already submitted an application."), code="invalid"
            )
        return cleaned_data

    def save(self, commit=True):
        self.instance = super().save(commit=False)
        team = Team.objects.create()

        self.instance.user = self.user
        self.instance.team = team

        if commit:
            self.instance.save()
            self.save_m2m()

        return self.instance
