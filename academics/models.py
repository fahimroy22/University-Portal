from django.db import models
from accounts.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Batch(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    batch_name = models.CharField(max_length=50)
    admission_year = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.department.code} - {self.batch_name}"


class Semester(models.Model):
    name = models.CharField(max_length=50)
    number = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=200)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'faculty'}
    )
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    section = models.CharField(max_length=20, default='A')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.code} - {self.batch} - Section {self.section}"


class CourseMaterial(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_offering.course.code} - {self.title}"