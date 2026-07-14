from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord, Mark

admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
admin.site.register(Mark)