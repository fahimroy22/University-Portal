from decimal import Decimal

from django.db import models

from accounts.models import User
from academics.models import Department, Semester
from students.models import StudentProfile

ADMISSION_CATEGORY_CHOICES = [
    ('regular', 'Regular'),
    ('diploma', 'Diploma'),
    ('masters', 'Masters'),
    ('special', 'Special'),
]


class ProgramFeeStructure(models.Model):
    PROGRAM_LEVEL_CHOICES = [
        ('undergraduate', 'Undergraduate'),
        ('diploma', 'Diploma'),
        ('postgraduate', 'Postgraduate'),
    ]

    program_name = models.CharField(max_length=150)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    level = models.CharField(
        max_length=30,
        choices=PROGRAM_LEVEL_CHOICES,
        default='undergraduate'
    )

    duration_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Example: 4 Yr / 8 Sem / 165"
    )

    admission_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    semester_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total_semesters = models.PositiveIntegerField(default=8)

    is_active = models.BooleanField(default=True)

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department__code', 'program_name']
        unique_together = ('program_name', 'department')

    @property
    def total_semester_fee_before_waiver(self):
        return self.semester_fee * self.total_semesters

    @property
    def grand_total_before_waiver(self):
        return self.admission_fee + self.total_semester_fee_before_waiver

    def __str__(self):
        if self.department:
            return f"{self.program_name} - {self.department.code}"
        return self.program_name


class WaiverPolicy(models.Model):
    program_fee = models.ForeignKey(
        ProgramFeeStructure,
        on_delete=models.CASCADE,
        related_name='waiver_policies',
        blank=True,
        null=True,
        help_text="Leave blank if this rule applies to all programs."
    )

    admission_category = models.CharField(
        max_length=30,
        choices=ADMISSION_CATEGORY_CHOICES,
        default='regular'
    )

    gpa_min = models.DecimalField(max_digits=4, decimal_places=2)
    gpa_max = models.DecimalField(max_digits=4, decimal_places=2)

    waiver_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Semester-wise waiver amount."
    )

    note = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Example: GPA 10 out of 10"
    )

    is_active = models.BooleanField(default=True)

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-gpa_min', '-gpa_max']

    def __str__(self):
        program = self.program_fee.program_name if self.program_fee else "All Programs"
        return f"{program}: GPA {self.gpa_min} - {self.gpa_max} = {self.waiver_amount}"


class FeeType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class StudentFinancialProfile(models.Model):
    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='financial_profile'
    )

    program_fee = models.ForeignKey(
        ProgramFeeStructure,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    admission_category = models.CharField(
        max_length=30,
        choices=ADMISSION_CATEGORY_CHOICES,
        default='regular'
    )

    ssc_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00')
    )

    hsc_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00')
    )

    combined_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00')
    )

    admission_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    semester_fee_before_waiver = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    regular_waiver_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Automatic waiver based on SSC + HSC GPA."
    )

    special_waiver_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Manual special waiver approved by Super Admin."
    )

    final_semester_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total_semesters = models.PositiveIntegerField(default=8)

    total_semester_fee_after_waiver = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    grand_total_after_waiver = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_financial_profiles'
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='updated_financial_profiles'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def recalculate(self):
        if self.program_fee:
            self.admission_fee = self.program_fee.admission_fee
            self.semester_fee_before_waiver = self.program_fee.semester_fee
            self.total_semesters = self.program_fee.total_semesters

        self.combined_gpa = (self.ssc_gpa or Decimal('0.00')) + (self.hsc_gpa or Decimal('0.00'))

        total_waiver = (self.regular_waiver_amount or Decimal('0.00')) + (self.special_waiver_amount or Decimal('0.00'))

        self.final_semester_fee = self.semester_fee_before_waiver - total_waiver

        if self.final_semester_fee < 0:
            self.final_semester_fee = Decimal('0.00')

        self.total_semester_fee_after_waiver = self.final_semester_fee * self.total_semesters
        self.grand_total_after_waiver = self.admission_fee + self.total_semester_fee_after_waiver

    def save(self, *args, **kwargs):
        self.recalculate()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.student_id} - Finance Profile"


class StudentFee(models.Model):
    FEE_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)

    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Final payable amount after waiver."
    )

    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    waiver_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    due_date = models.DateField(blank=True, null=True)

    is_paid = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=FEE_STATUS_CHOICES,
        default='unpaid'
    )

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_payment_status(self):
        if self.paid_amount >= self.amount:
            self.status = 'paid'
            self.is_paid = True
        elif self.paid_amount > 0:
            self.status = 'partial'
            self.is_paid = False
        else:
            self.status = 'unpaid'
            self.is_paid = False

    def save(self, *args, **kwargs):
        self.update_payment_status()
        super().save(*args, **kwargs)

    @property
    def due_amount(self):
        due = self.amount - self.paid_amount
        if due < 0:
            return Decimal('0.00')
        return due

    def __str__(self):
        return f"{self.student.student_id} - {self.fee_type.name} - {self.amount}"


class Payment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)

    received_by = models.CharField(max_length=100)

    payment_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Example: Cash, Bank, bKash, Card"
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.student_id} - Paid {self.amount}"


class Waiver(models.Model):
    WAIVER_SOURCE_CHOICES = [
        ('gpa', 'GPA Based'),
        ('special', 'Special Waiver'),
        ('manual', 'Manual Adjustment'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='waivers'
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    source = models.CharField(
        max_length=20,
        choices=WAIVER_SOURCE_CHOICES,
        default='manual'
    )

    reason = models.TextField()

    approved_by = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_id} - Waiver {self.amount}"