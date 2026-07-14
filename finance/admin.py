from django.contrib import admin

from .models import (
    ProgramFeeStructure,
    WaiverPolicy,
    FeeType,
    StudentFinancialProfile,
    StudentFee,
    Payment,
    Waiver,
)


@admin.register(ProgramFeeStructure)
class ProgramFeeStructureAdmin(admin.ModelAdmin):
    list_display = (
        'program_name',
        'department',
        'level',
        'admission_fee',
        'semester_fee',
        'total_semesters',
        'is_active',
    )
    list_filter = ('level', 'department', 'is_active')
    search_fields = ('program_name', 'department__code', 'department__name')


@admin.register(WaiverPolicy)
class WaiverPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'program_fee',
        'admission_category',
        'gpa_min',
        'gpa_max',
        'waiver_amount',
        'is_active',
    )
    list_filter = ('admission_category', 'is_active', 'program_fee')
    search_fields = ('program_fee__program_name', 'note')


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(StudentFinancialProfile)
class StudentFinancialProfileAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'program_fee',
        'admission_category',
        'combined_gpa',
        'admission_fee',
        'semester_fee_before_waiver',
        'regular_waiver_amount',
        'special_waiver_amount',
        'final_semester_fee',
        'grand_total_after_waiver',
    )
    list_filter = ('program_fee', 'admission_category')
    search_fields = (
        'student__student_id',
        'student__user__username',
        'student__user__first_name',
        'student__user__last_name',
        'program_fee__program_name',
    )


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'fee_type',
        'semester',
        'original_amount',
        'waiver_amount',
        'amount',
        'paid_amount',
        'due_amount',
        'status',
        'is_paid',
    )
    list_filter = ('fee_type', 'semester', 'status', 'is_paid')
    search_fields = (
        'student__student_id',
        'student__user__username',
        'fee_type__name',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'student_fee',
        'amount',
        'payment_date',
        'received_by',
        'payment_method',
        'transaction_id',
    )
    list_filter = ('payment_date', 'payment_method')
    search_fields = (
        'student__student_id',
        'student__user__username',
        'received_by',
        'transaction_id',
    )


@admin.register(Waiver)
class WaiverAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'student_fee',
        'amount',
        'source',
        'approved_by',
        'created_at',
    )
    list_filter = ('source', 'created_at')
    search_fields = (
        'student__student_id',
        'student__user__username',
        'approved_by',
    )