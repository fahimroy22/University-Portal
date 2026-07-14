from django.db import models
from django.utils import timezone

from accounts.models import User
from academics.models import Department, Batch


class Notice(models.Model):
    NOTICE_TYPE_CHOICES = [
        ('general', 'General'),
        ('academic', 'Academic'),
        ('exam', 'Exam'),
        ('payment', 'Payment'),
        ('admission', 'Admission'),
        ('event', 'Event'),
        ('urgent', 'Urgent'),
    ]

    TARGET_AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('students', 'Students'),
        ('faculty', 'Faculty'),
        ('department', 'Specific Department'),
        ('batch', 'Specific Batch'),
        ('exam_controller', 'Exam Controller'),
        ('accounts', 'Accounts Office'),
        ('admin', 'Admin'),
    ]

    title = models.CharField(max_length=200)

    message = models.TextField()

    notice_type = models.CharField(
        max_length=30,
        choices=NOTICE_TYPE_CHOICES,
        default='general'
    )

    target_audience = models.CharField(
        max_length=30,
        choices=TARGET_AUDIENCE_CHOICES,
        default='all'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    attachment = models.FileField(
        upload_to='notice_attachments/',
        blank=True,
        null=True
    )

    is_published = models.BooleanField(default=True)

    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    published_at = models.DateTimeField(default=timezone.now)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-id']

    def __str__(self):
        return f"{self.title} - {self.get_target_audience_display()}"