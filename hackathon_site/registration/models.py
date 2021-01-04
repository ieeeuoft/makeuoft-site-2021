from datetime import date
import uuid

from django.db import models
from django.core import validators
from django.contrib.auth import get_user_model

from registration.validators import UploadedFileValidator

User = get_user_model()


def _generate_team_code():
    team_code = uuid.uuid4().hex[:5].upper()
    while Team.objects.filter(team_code=team_code).exists():
        team_code = uuid.uuid4().hex[:5].upper()
    return team_code


class Team(models.Model):
    team_code = models.CharField(max_length=5, default=_generate_team_code, null=False)

    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    MAX_MEMBERS = 4

    def __str__(self):
        return self.team_code


class Application(models.Model):
    GENDER_CHOICES = [
        (None, ""),
        ("male", "Male"),
        ("female", "Female"),
        ("non-binary", "Non-binary"),
        ("other", "Other"),
        ("no-answer", "Prefer not to answer"),
    ]

    ETHNICITY_CHOICES = [
        (None, ""),
        ("american-native", "American Indian or Alaskan Native"),
        ("asian-pacific-islander", "Asian / Pacific Islander"),
        ("black-african-american", "Black or African American"),
        ("hispanic", "Hispanic"),
        ("caucasian", "White / Caucasian"),
        ("other", "Multiple ethnicity / Other"),
        ("no-answer", "Prefer not to answer"),
    ]

    STUDY_LEVEL_CHOICES = [
        (None, ""),
        ("undergraduate", "Undergraduate"),
        ("gradschool", "Graduate School"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    team = models.ForeignKey(
        Team, related_name="applications", on_delete=models.CASCADE, null=False
    )

    # User Submitted Fields
    birthday = models.DateField(
        null=False,
        validators=[
            validators.MaxValueValidator(
                date(2003, 2, 6),
                message="You must be over 18 years old on February 6, 2021 to participate in MakeUofT.",
            )
        ],
    )
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, null=False)
    ethnicity = models.CharField(max_length=50, choices=ETHNICITY_CHOICES, null=False)
    school = models.CharField(help_text="University", max_length=255, null=False,)
    study_level = models.CharField(
        max_length=50, choices=STUDY_LEVEL_CHOICES, null=False
    )
    graduation_year = models.IntegerField(
        null=False,
        validators=[
            validators.MinValueValidator(
                2000, message="Enter a realistic graduation year."
            ),
            validators.MaxValueValidator(
                2030, message="Enter a realistic graduation year."
            ),
        ],
    )
    resume = models.FileField(
        upload_to="applications/resumes/",
        validators=[
            UploadedFileValidator(
                content_types=["application/pdf"], max_upload_size=20 * 1024 * 1024
            )
        ],
        null=False,
    )
    resume_sharing = models.BooleanField(
        help_text="I consent to IEEE UofT sharing my resume with event sponsors (optional).",
        default=False,
        null=False,
    )
    eligibility_agree = models.BooleanField(
        help_text="I confirm that I will be over 18 years old and a university student "
        "on February 6, 2021.",
        blank=False,
        null=False,
    )
    conduct_agree = models.BooleanField(
        help_text="I have read and agree to the "
        '<a href="https://docs.google.com/document/d/1RH36R1nt8KQfKtd2YoNAJNuaCW5um55a6oVP_bWRK6U/edit" target="_blank">code of conduct</a>.',
        blank=False,
        null=False,
    )
    data_agree = models.BooleanField(
        help_text="I consent to have the data in this application collected for event purposes "
        "including administration, ranking, and event communication.",
        blank=False,
        null=False,
    )

    rsvp = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
