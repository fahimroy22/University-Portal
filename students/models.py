from django.db import models

from accounts.models import User
from academics.models import Department, Batch, Semester, CourseOffering


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    student_id = models.CharField(
        max_length=30,
        unique=True
    )
    photo = models.ImageField(

        upload_to='student_photos/',

        blank=True,

        null=True

    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True
    )

    current_semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True
    )

    admission_session = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Example: Spring 2026, Summer 2026, Fall 2026"
    )

    guardian_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    guardian_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.username}"


class CourseRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course_offering')

    def __str__(self):
        return f"{self.student.student_id} - {self.course_offering.course.code} - {self.status}"