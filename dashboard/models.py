from django.db import models
from django.utils import timezone

from accounts.models import User



class AuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    action = models.CharField(max_length=100)

    module = models.CharField(max_length=100)

    description = models.TextField(
        blank=True,
        null=True
    )

    target_model = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    target_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    target_repr = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        actor_name = self.actor.username if self.actor else "Unknown"
        return f"{actor_name} - {self.action} - {self.module}"


class SystemSettings(models.Model):
    university_name = models.CharField(
        max_length=200,
        default='University of Global Village'
    )

    short_name = models.CharField(
        max_length=50,
        default='UGV'
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    contact_email = models.EmailField(
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    logo = models.ImageField(
        upload_to='system_settings/',
        blank=True,
        null=True
    )

    current_academic_session = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Example: Summer 2026'
    )

    result_publication_note = models.TextField(
        blank=True,
        null=True,
        default='This result is published electronically by the university authority.'
    )

    admit_card_note = models.TextField(
        blank=True,
        null=True,
        default='Students must bring this admit card to the examination hall.'
    )

    payment_instruction = models.TextField(
        blank=True,
        null=True,
        default='Please clear all dues before the payment deadline.'
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"{self.short_name} System Settings"