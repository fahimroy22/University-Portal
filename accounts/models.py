from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('dept_head', 'Department Head'),
        ('exam_controller', 'Exam Controller'),
        ('accounts', 'Accounts Officer'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='student'
    )

    employee_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique ID for faculty/staff/admin users. Example: FAC-CSE-001, ACC-001, EXAM-001"
    )

    staff_department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='staff_users',
        help_text="Department for faculty, department head, or staff if applicable."
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Example: Lecturer, Assistant Professor, Accounts Officer, Exam Controller"
    )

    office_room = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True
    )

    def __str__(self):
        if self.employee_id:
            return f"{self.employee_id} - {self.username} - {self.get_role_display()}"

        return f"{self.username} - {self.get_role_display()}"