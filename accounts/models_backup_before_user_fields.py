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

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"