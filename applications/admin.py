from django.contrib import admin
from .models import StudentApplication


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'to_user',
        'subject',
        'status',
        'submitted_at',
    )

    list_filter = (
        'status',
        'submitted_at',
    )

    search_fields = (
        'student__student_id',
        'student__user__username',
        'subject',
        'message',
    )

    readonly_fields = (
        'submitted_at',
        'updated_at',
    )