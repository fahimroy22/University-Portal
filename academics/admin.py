from django.contrib import admin
from .models import Department, Batch, Semester, Course, CourseOffering
from .models import Department, Batch, Semester, Course, CourseOffering, CourseMaterial
admin.site.register(Department)
admin.site.register(Batch)
admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(CourseOffering)
admin.site.register(CourseMaterial)