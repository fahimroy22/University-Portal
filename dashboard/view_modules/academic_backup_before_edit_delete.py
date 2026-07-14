from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.models import User
from academics.models import Department, Batch, Semester, Course, CourseOffering


@login_required
def academic_setup(request):
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    departments = Department.objects.all().order_by('code')

    batches = Batch.objects.select_related(
        'department'
    ).order_by(
        'department__code',
        'batch_name'
    )

    semesters = Semester.objects.all().order_by('number')

    courses = Course.objects.select_related(
        'department',
        'semester'
    ).order_by(
        'department__code',
        'code'
    )

    faculty_users = User.objects.filter(
        role='faculty',
        is_active=True
    ).order_by('username')

    course_offerings = CourseOffering.objects.select_related(
        'course',
        'course__department',
        'faculty',
        'batch',
        'batch__department',
        'semester'
    ).order_by(
        'course__department__code',
        'semester__number',
        'course__code'
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_department':
            name = request.POST.get('name')
            code = request.POST.get('code')

            if name and code:
                Department.objects.get_or_create(
                    code=code.upper(),
                    defaults={
                        'name': name
                    }
                )
                messages.success(request, "Department created successfully.")
            else:
                messages.error(request, "Please enter department name and code.")

            return redirect('academic_setup')

        elif action == 'create_batch':
            department_id = request.POST.get('department')
            batch_name = request.POST.get('batch_name')
            admission_year = request.POST.get('admission_year')

            department = Department.objects.filter(id=department_id).first()

            if department and batch_name and admission_year:
                Batch.objects.create(
                    department=department,
                    batch_name=batch_name,
                    admission_year=admission_year
                )
                messages.success(request, "Batch created successfully.")
            else:
                messages.error(request, "Please fill all batch fields.")

            return redirect('academic_setup')

        elif action == 'create_semester':
            name = request.POST.get('name')
            number = request.POST.get('number')

            if name and number:
                Semester.objects.get_or_create(
                    number=number,
                    defaults={
                        'name': name
                    }
                )
                messages.success(request, "Semester created successfully.")
            else:
                messages.error(request, "Please enter semester name and number.")

            return redirect('academic_setup')

        elif action == 'create_course':
            department_id = request.POST.get('department')
            code = request.POST.get('code')
            title = request.POST.get('title')
            credit = request.POST.get('credit')
            semester_id = request.POST.get('semester')

            department = Department.objects.filter(id=department_id).first()
            semester = Semester.objects.filter(id=semester_id).first()

            if department and code and title and credit and semester:
                Course.objects.get_or_create(
                    code=code.upper(),
                    defaults={
                        'department': department,
                        'title': title,
                        'credit': credit,
                        'semester': semester,
                    }
                )
                messages.success(request, "Course created successfully.")
            else:
                messages.error(request, "Please fill all course fields.")

            return redirect('academic_setup')

        elif action == 'create_course_offering':
            course_id = request.POST.get('course')
            faculty_id = request.POST.get('faculty')
            batch_id = request.POST.get('batch')
            semester_id = request.POST.get('semester')
            section = request.POST.get('section') or 'A'
            is_active = request.POST.get('is_active') == 'on'

            course = Course.objects.filter(id=course_id).first()

            faculty = User.objects.filter(
                id=faculty_id,
                role='faculty'
            ).first()

            batch = Batch.objects.filter(id=batch_id).first()
            semester = Semester.objects.filter(id=semester_id).first()

            if course and batch and semester:
                CourseOffering.objects.create(
                    course=course,
                    faculty=faculty,
                    batch=batch,
                    semester=semester,
                    section=section,
                    is_active=is_active
                )
                messages.success(request, "Course offering created successfully.")
            else:
                messages.error(request, "Please select course, batch, and semester.")

            return redirect('academic_setup')

    context = {
        'departments': departments,
        'batches': batches,
        'semesters': semesters,
        'courses': courses,
        'faculty_users': faculty_users,
        'course_offerings': course_offerings,
    }

    return render(request, 'dashboard/academic_setup.html', context)


@login_required
def dept_head_dashboard(request):
    return render(request, 'dashboard/dept_head_dashboard.html')


@login_required
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html')


@login_required
def super_admin_dashboard(request):
    return render(request, 'dashboard/super_admin_dashboard.html')