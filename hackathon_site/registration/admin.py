import csv
import functools

from django.contrib import admin
from django.http import HttpResponse

from registration.models import Application, Team as TeamApplied


def rgetattr(obj, attr, *args):
    """
    Recursive getattr, allows for nested attributes.
    For example if you're in the Application class, you can't do getattr for user.first_name
    But with rgetattr you can.
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class ApplicationInline(admin.TabularInline):
    model = Application
    autocomplete_fields = ("user",)
    extra = 0


class ExportCsvMixin:
    export_field_names = []
    export_field_attributes = []

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(
            self.model._meta
        )
        writer = csv.writer(response)

        writer.writerow(self.export_field_names)
        for obj in queryset:
            attributes = [
                rgetattr(obj, field) for field in self.export_field_attributes
            ]
            row = writer.writerow(attributes)

        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(TeamApplied)
class TeamAppliedAdmin(admin.ModelAdmin):
    search_fields = ("id", "team_code")
    list_display = ("team_code", "get_members_count")
    inlines = (ApplicationInline,)

    def get_members_count(self, obj):
        return obj.applications.count()

    get_members_count.short_description = "Members"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("applications")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin, ExportCsvMixin):
    autocomplete_fields = ("user", "team")
    list_display = ("get_full_name", "team", "school")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "team__team_code",
    )
    list_filter = ("school",)
    actions = ["export_as_csv"]

    export_field_names = [
        "First Name",
        "Last Name",
        "Email",
        "Team Code",
        "Birthday",
        "Gender",
        "Ethnicity",
        "School",
        "Study Level",
        "Graduation Year",
        "Resume Sharing",
        "Review Status",
        "RSVP",
        "Created At",
        "Updated At",
    ]
    export_field_attributes = [
        "user.first_name",
        "user.last_name",
        "user",
        "team",
        "birthday",
        "gender",
        "ethnicity",
        "school",
        "study_level",
        "graduation_year",
        "resume_sharing",
        "review.status",
        "rsvp",
        "created_at",
        "updated_at",
    ]

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_full_name.short_description = "User"
