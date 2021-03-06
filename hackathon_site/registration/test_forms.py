from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from django_registration import validators

from hackathon_site.tests import SetupUserMixin
from registration.models import User, Team, Application
from registration.forms import SignUpForm, ApplicationForm


class SignUpFormTestCase(TestCase):
    def test_fields_required(self):
        form = SignUpForm()
        for field in (
            User.get_email_field_name(),
            "first_name",
            "last_name",
            "password1",
            "password2",
        ):
            self.assertTrue(form.fields[field].required)

    def test_has_email_validators(self):
        """
        Test that the necessary validators for email have been added.
        """
        form = SignUpForm()
        email_validators = form.fields["email"].validators
        self.assertTrue(
            any(isinstance(v, validators.HTML5EmailValidator) for v in email_validators)
        )
        self.assertTrue(validators.validate_confusables_email in email_validators)
        self.assertTrue(
            any(
                isinstance(v, validators.CaseInsensitiveUnique)
                for v in email_validators
            )
        )

    def test_email_uniqueness(self):
        """
        Test that the case insensitive validator for email was configured correctly
        """
        User.objects.create_user(
            username="foo@bar.com", email="foo@bar.com", password="foobar123"
        )
        data = {
            "email": "FOO@bar.com",
            "first_name": "Foo",
            "last_name": "Bar",
            "password1": "abcdef456",
            "password2": "abcdef456",
        }

        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("This email is unavailable", form.errors["email"])

    def test_sets_username_to_email(self):
        data = {
            "email": "foo@bar.com",
            "first_name": "Foo",
            "last_name": "Bar",
            "password1": "abcdef456",
            "password2": "abcdef456",
        }
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user, User.objects.first())
        self.assertEqual(user.username, user.email)
        self.assertEqual(user.email, data["email"])


class ApplicationFormTestCase(SetupUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.data = {
            "birthday": date(2000, 9, 8),
            "gender": "no-answer",
            "ethnicity": "no-answer",
            "school": "UofT",
            "study_level": "undergraduate",
            "graduation_year": 2020,
            "resume_sharing": False,
            "eligibility_agree": True,
            "conduct_agree": True,
            "data_agree": True,
        }
        self.files = self._build_files()

    @staticmethod
    def _build_files(name="my_resume.pdf", size=12, content_type="application/pdf"):
        return {
            "resume": InMemoryUploadedFile(
                BytesIO(b"some_content"),
                None,
                name,
                content_type,
                size,  # We're cheating by not making this the real size of the bytes
                # object, but this is the attribute that the validator checks.
                None,
                None,
            )
        }

    def _build_form(self, user=None, data=None, files=None):
        if user is None:
            user = self.user
        if data is None:
            data = self.data
        if files is None:
            files = self.files

        return ApplicationForm(user=user, data=data, files=files)

    def test_fields_are_required(self):
        for field in self.data:
            if field == "resume_sharing":
                continue

            bad_data = self.data.copy()
            del bad_data[field]

            form = self._build_form(data=bad_data)
            self.assertFalse(form.is_valid(), msg=field)
            self.assertIn(field, form.errors, msg=field)
            self.assertIn("This field is required.", form.errors[field], msg=field)

        # File field
        form = self._build_form(files={})
        self.assertFalse(form.is_valid())
        self.assertIn("resume", form.errors)
        self.assertIn("This field is required.", form.errors["resume"])

    def test_user_already_has_application(self):
        team = Team.objects.create()
        Application.objects.create(
            user=self.user, team=team, resume="resume.pdf", **self.data
        )

        form = self._build_form()
        self.assertFalse(form.is_valid())
        self.assertIn(
            "User has already submitted an application.", form.non_field_errors()
        )

    def test_saving_adds_team_and_user(self):
        form = self._build_form()
        self.assertTrue(form.is_valid())
        instance = form.save()

        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(Application.objects.first(), instance)
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(Team.objects.first(), instance.team)
        self.assertEqual(instance.user, self.user)

    def test_does_not_save_when_commit_false(self):
        form = self._build_form()
        form.save(commit=False)

        self.assertEqual(Team.objects.count(), 1)  # Team still gets created for the FK
        self.assertEqual(Application.objects.count(), 0)

    def test_graduation_year_validator(self):
        def assert_bad_graduation_year(form):
            self.assertFalse(form.is_valid())
            self.assertIn(
                "Enter a realistic graduation year.", form.errors["graduation_year"]
            )

        year_min = 2000
        year_max = 2030

        data = self.data.copy()
        data["graduation_year"] = year_min - 1
        form = self._build_form(data=data)
        assert_bad_graduation_year(form)

        data["graduation_year"] = year_min
        form = self._build_form(data=data)
        self.assertTrue(form.is_valid())

        data["graduation_year"] = year_max
        form = self._build_form(data=data)
        self.assertTrue(form.is_valid())

        data["graduation_year"] = year_max + 1
        form = self._build_form(data=data)
        assert_bad_graduation_year(form)

    def test_birthday_validator(self):
        def assert_bad_birthday(form):
            self.assertFalse(form.is_valid())
            self.assertIn(
                "You must be over 18 years old on February 6, 2021 to participate in MakeUofT.",
                form.errors["birthday"],
            )

        birthday_min = date(2003, 2, 6)

        data = self.data.copy()
        data["birthday"] = birthday_min + timedelta(days=1)
        form = self._build_form(data=data)
        assert_bad_birthday(form)

        data["birthday"] = birthday_min
        form = self._build_form(data=data)
        self.assertTrue(form.is_valid())

    def test_resume_wrong_type(self):
        files = self._build_files(name="my_resume.jpg", content_type="image/jpeg")
        form = self._build_form(files=files)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Unsupported file type: image/jpeg. Allowed file types: application/pdf.",
            form.errors["resume"],
        )

    def test_resume_too_big(self):
        # Maximum allowed size is 20 MB
        files = self._build_files(size=20 * 1024 * 1024 + 1)
        form = self._build_form(files=files)
        self.assertFalse(form.is_valid())
        # \xa0 is non-breaking space, put there automatically
        self.assertIn(
            "File must be no bigger than 20.0\xa0MB. Currently 20.0\xa0MB.",
            form.errors["resume"],
        )

    @patch("registration.forms.is_registration_open")
    def test_registration_has_closed(self, mock_is_registration_open):
        mock_is_registration_open.return_value = False
        form = self._build_form()
        self.assertFalse(form.is_valid())
        self.assertIn("Registration has closed.", form.non_field_errors())
