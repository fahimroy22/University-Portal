from decimal import Decimal

from django.db import models

from accounts.models import User
from academics.models import CourseOffering
from students.models import StudentProfile


class AttendanceSession(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    date = models.DateField()
    topic = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.course_offering.course.code} - {self.date}"


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.student_id} - {status}"


class Mark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)

    class_test = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assignment = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attendance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    midterm = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    raw_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=5, blank=True, null=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    is_submitted = models.BooleanField(default=False)

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_marks'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_marks'
    )
    last_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course_offering')
        ordering = ['course_offering__course__code', 'student__student_id']

    def save(self, *args, **kwargs):
        self.raw_total = (
            self.class_test +
            self.assignment +
            self.attendance +
            self.midterm +
            self.final
        )

        self.total = round((self.raw_total / Decimal('150')) * Decimal('100'), 2)

        if self.total >= 80:
            self.grade = 'A+'
            self.grade_point = Decimal('4.00')
        elif self.total >= 75:
            self.grade = 'A'
            self.grade_point = Decimal('3.75')
        elif self.total >= 70:
            self.grade = 'A-'
            self.grade_point = Decimal('3.50')
        elif self.total >= 65:
            self.grade = 'B+'
            self.grade_point = Decimal('3.25')
        elif self.total >= 60:
            self.grade = 'B'
            self.grade_point = Decimal('3.00')
        elif self.total >= 55:
            self.grade = 'B-'
            self.grade_point = Decimal('2.75')
        elif self.total >= 50:
            self.grade = 'C+'
            self.grade_point = Decimal('2.50')
        elif self.total >= 45:
            self.grade = 'C'
            self.grade_point = Decimal('2.25')
        elif self.total >= 40:
            self.grade = 'D'
            self.grade_point = Decimal('2.00')
        else:
            self.grade = 'F'
            self.grade_point = Decimal('0.00')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering.course.code}"


class Assignment(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField()
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)

    is_published = models.BooleanField(default=True)
    accepting_submissions = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course_offering.course.code} - {self.title}"


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('checked', 'Checked'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    answer_text = models.TextField(blank=True, null=True)
    submitted_file = models.FileField(
        upload_to='assignment_submissions/',
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(auto_now=True)

    obtained_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    feedback = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.student_id} - {self.assignment.title}"