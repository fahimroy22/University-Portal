from django.contrib import admin
from .models import ExamRoutine, AdmitCard, SeatPlan, HallDuty, ResultPublication


@admin.register(ExamRoutine)
class ExamRoutineAdmin(admin.ModelAdmin):
    list_display = (
        'course_offering',
        'exam_type',
        'exam_date',
        'start_time',
        'end_time',
        'room',
        'is_published',
    )
    list_filter = ('exam_type', 'is_published', 'exam_date')
    search_fields = ('course_offering__course__code', 'course_offering__course__title', 'room')


@admin.register(AdmitCard)
class AdmitCardAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'exam_type',
        'is_eligible',
        'is_published',
        'generated_at',
    )
    list_filter = ('exam_type', 'is_eligible', 'is_published')


@admin.register(SeatPlan)
class SeatPlanAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'course_offering',
        'exam_type',
        'room',
        'seat_number',
        'is_published',
    )
    list_filter = ('exam_type', 'is_published', 'room')
    search_fields = ('student__student_id', 'student__user__username', 'room', 'seat_number')


@admin.register(HallDuty)
class HallDutyAdmin(admin.ModelAdmin):
    list_display = (
        'faculty',
        'exam_routine',
        'duty_room',
    )
    search_fields = ('faculty__username', 'duty_room')


@admin.register(ResultPublication)
class ResultPublicationAdmin(admin.ModelAdmin):
    list_display = (
        'course_offering',
        'exam_type',
        'is_published',
        'published_by',
        'published_at',
    )
    list_filter = ('exam_type', 'is_published')