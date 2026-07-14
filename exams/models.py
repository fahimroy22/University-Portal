from django.db import models, transaction
from django.utils import timezone
from django.core.validators import FileExtensionValidator

from accounts.models import User
from academics.models import CourseOffering
from students.models import StudentProfile


class ExamRoutine(models.Model):
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('recovery', 'Recovery'),
    ]

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    is_published = models.BooleanField(default=False)

    class Meta:
        unique_together = ('course_offering', 'exam_type')

    def __str__(self):
        return f"{self.course_offering.course.code} - {self.get_exam_type_display()}"


class AdmitCard(models.Model):
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default='final'
    )
    is_eligible = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'exam_type')

    def __str__(self):
        return f"Admit Card - {self.student.student_id} - {self.get_exam_type_display()}"


class SeatPlan(models.Model):
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    room = models.CharField(max_length=50)
    seat_number = models.CharField(max_length=30)
    is_published = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course_offering', 'exam_type')

    def __str__(self):
        return (
            f"{self.student.student_id} - "
            f"{self.course_offering.course.code} - "
            f"{self.get_exam_type_display()} - "
            f"Seat {self.seat_number}"
        )


class HallDuty(models.Model):
    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'faculty'}
    )
    exam_routine = models.ForeignKey(ExamRoutine, on_delete=models.CASCADE)
    duty_room = models.CharField(max_length=50)
    duty_note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('faculty', 'exam_routine', 'duty_room')

    def __str__(self):
        return (
            f"{self.faculty.username} - "
            f"{self.exam_routine.course_offering.course.code} - "
            f"{self.duty_room}"
        )


class ResultPublication(models.Model):
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
    ]

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default='final'
    )
    is_published = models.BooleanField(default=False)

    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('course_offering', 'exam_type')

    def publish(self, user):
        self.is_published = True
        self.published_by = user
        self.published_at = timezone.now()
        self.save()

    def unpublish(self):
        self.is_published = False
        self.published_at = None
        self.save()

    def __str__(self):
        status = 'Published' if self.is_published else 'Unpublished'
        return (
            f"{self.course_offering.course.code} - "
            f"{self.get_exam_type_display()} - "
            f"{status}"
        )


class StudentMarkReviewRequest(models.Model):
    """
    A student-facing request asking the responsible faculty member
    to review a possibly incorrect published or recorded result.

    This model does NOT directly change official marks.
    """

    STATUS_CHOICES = [
        ('pending_faculty', 'Pending Faculty Review'),
        ('faculty_rejected', 'Rejected by Faculty'),
        ('faculty_confirmed', 'Confirmed by Faculty'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='mark_review_requests'
    )

    mark = models.ForeignKey(
        'faculty.Mark',
        on_delete=models.CASCADE,
        related_name='student_review_requests'
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='student_mark_review_requests'
    )

    reason = models.TextField()

    requested_components = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'Mark components selected by the student, such as '
            'class_test, assignment, attendance, midterm, or final.'
        )
    )

    attachment = models.FileField(
        upload_to='mark_review_requests/student/%Y/%m/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf',
                    'jpg',
                    'jpeg',
                    'png',
                ]
            )
        ]
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_faculty'
    )

    faculty_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_student_mark_requests'
    )

    faculty_note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    faculty_reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def confirm_by_faculty(self, user, note=''):
        self.status = 'faculty_confirmed'
        self.faculty_reviewed_by = user
        self.faculty_reviewed_at = timezone.now()
        self.faculty_note = note
        self.save(
            update_fields=[
                'status',
                'faculty_reviewed_by',
                'faculty_reviewed_at',
                'faculty_note',
            ]
        )

    def reject_by_faculty(self, user, note=''):
        self.status = 'faculty_rejected'
        self.faculty_reviewed_by = user
        self.faculty_reviewed_at = timezone.now()
        self.faculty_note = note
        self.save(
            update_fields=[
                'status',
                'faculty_reviewed_by',
                'faculty_reviewed_at',
                'faculty_note',
            ]
        )

    def __str__(self):
        return (
            f"{self.student.student_id} - "
            f"{self.course_offering.course.code} - "
            f"{self.status}"
        )


class ResultCorrectionRequest(models.Model):
    """
    Official proposed mark correction.

    Intended workflow:

    Faculty submits
        -> Exam Controller verifies
        -> Super Admin approves/rejects
        -> Official Mark record is updated only on approval.

    The legacy 'pending' status is temporarily preserved so the
    currently working correction workflow remains compatible while
    the new multi-stage workflow is introduced.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Temporary legacy compatibility
        ('faculty_submitted', 'Submitted by Faculty'),
        ('exam_verified', 'Verified by Exam Controller'),
        ('exam_rejected', 'Rejected by Exam Controller'),
        ('approved', 'Approved by Super Admin'),
        ('rejected', 'Rejected by Super Admin'),
    ]

    mark = models.ForeignKey(
        'faculty.Mark',
        on_delete=models.CASCADE,
        related_name='correction_requests'
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE
    )

    # Optional originating student request.
    # Null means the faculty discovered the error independently.
    student_review_request = models.ForeignKey(
        StudentMarkReviewRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='correction_requests'
    )

    # Normally the faculty member who creates the official request.
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='result_correction_requests'
    )

    reason = models.TextField()

    faculty_attachment = models.FileField(
        upload_to='result_corrections/faculty/%Y/%m/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf',
                    'jpg',
                    'jpeg',
                    'png',
                ]
            )
        ]
    )

    # Snapshot of the official mark before correction.
    old_class_test = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    old_assignment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    old_attendance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    old_midterm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    old_final = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # Exact values proposed by the faculty.
    new_class_test = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    new_assignment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    new_attendance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    new_midterm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    new_final = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # -----------------------------------------------------
    # Exam Controller verification
    # -----------------------------------------------------

    exam_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exam_reviewed_result_corrections'
    )

    exam_reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    exam_note = models.TextField(
        blank=True,
        null=True
    )

    exam_attachment = models.FileField(
        upload_to='result_corrections/exam_controller/%Y/%m/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf',
                    'jpg',
                    'jpeg',
                    'png',
                ]
            )
        ]
    )

    # -----------------------------------------------------
    # Final Super Admin review
    # -----------------------------------------------------

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_result_corrections'
    )

    admin_note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def verify_by_exam_controller(
        self,
        user,
        note='',
        attachment=None
    ):
        """
        Exam Controller verifies the faculty request and forwards it
        to the Super Admin queue.
        """

        self.status = 'exam_verified'
        self.exam_reviewed_by = user
        self.exam_reviewed_at = timezone.now()
        self.exam_note = note

        if attachment:
            self.exam_attachment = attachment

        self.save()

    def reject_by_exam_controller(
        self,
        user,
        note=''
    ):
        """
        Exam Controller rejects the faculty correction request.
        No official marks are changed.
        """

        self.status = 'exam_rejected'
        self.exam_reviewed_by = user
        self.exam_reviewed_at = timezone.now()
        self.exam_note = note

        self.save()

    def approve(
        self,
        user,
        note=''
    ):
        """
        Final approval.

        The official Mark record and correction request are updated
        inside one database transaction.
        """

        with transaction.atomic():
            self.mark.class_test = self.new_class_test
            self.mark.assignment = self.new_assignment
            self.mark.attendance = self.new_attendance
            self.mark.midterm = self.new_midterm
            self.mark.final = self.new_final

            self.mark.last_updated_by = user
            self.mark.last_updated_at = timezone.now()

            self.mark.save()

            self.status = 'approved'
            self.reviewed_by = user
            self.reviewed_at = timezone.now()
            self.admin_note = note

            self.save()

    def reject(
        self,
        user,
        note=''
    ):
        """
        Final Super Admin rejection.

        No official marks are changed.
        """

        self.status = 'rejected'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.admin_note = note

        self.save()

    def __str__(self):
        return (
            f"{self.student.student_id} - "
            f"{self.course_offering.course.code} - "
            f"{self.status}"
        )

