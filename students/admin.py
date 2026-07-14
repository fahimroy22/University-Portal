from django.contrib import admin
from .models import StudentProfile, CourseRegistration


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        'student_id',
        'user',
        'department',
        'batch',
        'current_semester',
        'is_active',
    )

    list_filter = (
        'department',
        'batch',
        'current_semester',
        'is_active',
    )

    search_fields = (
        'student_id',
        'user__username',
        'user__first_name',
        'user__last_name',
    )

    fields = (
        'user',
        'student_id',
        'photo',
        'department',
        'batch',
        'current_semester',
        'admission_session',
        'guardian_name',
        'guardian_phone',
        'address',
        'cgpa',
        'is_active',
    )


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'course_offering',
        'status',
        'registered_at',
    )

    list_filter = (
        'status',
        'registered_at',
    )

    search_fields = (
        'student__student_id',
        'student__user__username',
        'course_offering__course__code',
        'course_offering__course__title',
    )