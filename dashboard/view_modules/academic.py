from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect

from accounts.models import User
from academics.models import (
    Department,
    Batch,
    Semester,
    Course,
    CourseOffering,
    CourseMaterial,
)
from students.models import StudentProfile, CourseRegistration
from faculty.models import AttendanceSession, Mark, Assignment
from exams.models import ExamRoutine, SeatPlan
from dashboard.view_modules.audit import create_audit_log


# ============================================================
# ACADEMIC SETUP
# ============================================================

@login_required
def academic_setup(request):
    if request.user.role not in ['admin', 'super_admin']:
        return redirect('dashboard')

    # ========================================================
    # HELPERS
    # ========================================================

    valid_tabs = {
        'departments',
        'batches',
        'semesters',
        'courses',
        'offerings',
    }

    def normalize_tab(tab_name):
        if tab_name in valid_tabs:
            return tab_name
        return 'departments'

    def redirect_to_academic_tab(tab_name):
        """
        Redirect back to Academic Setup after POST.

        The future HTML file can send:
            <input
                type="hidden"
                name="return_query"
                value="{{ request.GET.urlencode }}"
            >

        This preserves filters, page number, and active tab.
        """

        tab_name = normalize_tab(tab_name)

        return_query = request.POST.get(
            'return_query',
            ''
        ).strip()

        if return_query:
            return redirect(
                f"{request.path}?{return_query}"
            )

        return redirect(
            f"{request.path}?{urlencode({'tab': tab_name})}"
        )

    def build_query_string_without(*excluded_keys):
        """
        Keeps all current GET parameters except specified keys.

        Useful for pagination links such as:

            ?{{ batch_query_string }}&batch_page=2
        """

        params = request.GET.copy()

        for key in excluded_keys:
            params.pop(key, None)

        return params.urlencode()

    # ========================================================
    # ACTIVE TAB
    # ========================================================

    active_tab = normalize_tab(
        request.GET.get(
            'tab',
            'departments'
        )
    )

    # ========================================================
    # POST ACTIONS
    # ========================================================

    if request.method == 'POST':
        action = request.POST.get('action')

        # ----------------------------------------------------
        # DEPARTMENT: CREATE
        # ----------------------------------------------------

        if action == 'create_department':
            name = request.POST.get(
                'name',
                ''
            ).strip()

            code = request.POST.get(
                'code',
                ''
            ).strip()

            if name and code:
                department, created = Department.objects.get_or_create(
                    code=code.upper(),
                    defaults={
                        'name': name
                    }
                )

                if created:
                    create_audit_log(
                        request,
                        action='CREATE',
                        module='Academic Setup',
                        description=(
                            f'Created department: '
                            f'{department.code} - '
                            f'{department.name}'
                        ),
                        target_model='Department',
                        target_id=department.id,
                        target_repr=(
                            f'{department.code} - '
                            f'{department.name}'
                        ),
                    )

                    messages.success(
                        request,
                        "Department created successfully."
                    )

                else:
                    messages.warning(
                        request,
                        "Department already exists."
                    )

            else:
                messages.error(
                    request,
                    "Please enter department name and code."
                )

            return redirect_to_academic_tab(
                'departments'
            )

        # ----------------------------------------------------
        # DEPARTMENT: UPDATE
        # ----------------------------------------------------

        elif action == 'update_department':
            department_id = request.POST.get(
                'department_id'
            )

            name = request.POST.get(
                'name',
                ''
            ).strip()

            code = request.POST.get(
                'code',
                ''
            ).strip()

            department = Department.objects.filter(
                id=department_id
            ).first()

            if department and name and code:
                code = code.upper()

                duplicate = Department.objects.exclude(
                    id=department.id
                ).filter(
                    code=code
                ).exists()

                if duplicate:
                    messages.error(
                        request,
                        "Another department already uses this code."
                    )

                else:
                    old_repr = (
                        f'{department.code} - '
                        f'{department.name}'
                    )

                    department.name = name
                    department.code = code
                    department.save()

                    create_audit_log(
                        request,
                        action='UPDATE',
                        module='Academic Setup',
                        description=(
                            f'Updated department from '
                            f'{old_repr} to '
                            f'{department.code} - '
                            f'{department.name}'
                        ),
                        target_model='Department',
                        target_id=department.id,
                        target_repr=(
                            f'{department.code} - '
                            f'{department.name}'
                        ),
                    )

                    messages.success(
                        request,
                        "Department updated successfully."
                    )

            else:
                messages.error(
                    request,
                    "Invalid department update request."
                )

            return redirect_to_academic_tab(
                'departments'
            )

        # ----------------------------------------------------
        # DEPARTMENT: DELETE
        # ----------------------------------------------------

        elif action == 'delete_department':
            department_id = request.POST.get(
                'department_id'
            )

            department = Department.objects.filter(
                id=department_id
            ).first()

            if department:
                has_batches = Batch.objects.filter(
                    department=department
                ).exists()

                has_courses = Course.objects.filter(
                    department=department
                ).exists()

                has_students = StudentProfile.objects.filter(
                    department=department
                ).exists()

                if (
                    has_batches or
                    has_courses or
                    has_students
                ):
                    messages.error(
                        request,
                        (
                            "Cannot delete this department because "
                            "it has batches, courses, or students."
                        )
                    )

                else:
                    department_id_value = department.id

                    department_repr = (
                        f'{department.code} - '
                        f'{department.name}'
                    )

                    create_audit_log(
                        request,
                        action='DELETE',
                        module='Academic Setup',
                        description=(
                            f'Deleted department: '
                            f'{department_repr}'
                        ),
                        target_model='Department',
                        target_id=department_id_value,
                        target_repr=department_repr,
                    )

                    department.delete()

                    messages.success(
                        request,
                        "Department deleted successfully."
                    )

            else:
                messages.error(
                    request,
                    "Department not found."
                )

            return redirect_to_academic_tab(
                'departments'
            )

        # ----------------------------------------------------
        # BATCH: CREATE
        # ----------------------------------------------------

        elif action == 'create_batch':
            department_id = request.POST.get(
                'department'
            )

            batch_name = request.POST.get(
                'batch_name',
                ''
            ).strip()

            admission_year = request.POST.get(
                'admission_year'
            )

            department = None

            if department_id:
                department = Department.objects.filter(
                    id=department_id
                ).first()

            if (
                department and
                batch_name and
                admission_year
            ):
                batch = Batch.objects.create(
                    department=department,
                    batch_name=batch_name,
                    admission_year=admission_year
                )

                create_audit_log(
                    request,
                    action='CREATE',
                    module='Academic Setup',
                    description=(
                        f'Created batch: '
                        f'{batch.department.code} - '
                        f'{batch.batch_name}'
                    ),
                    target_model='Batch',
                    target_id=batch.id,
                    target_repr=(
                        f'{batch.department.code} - '
                        f'{batch.batch_name}'
                    ),
                )

                messages.success(
                    request,
                    "Batch created successfully."
                )

            else:
                messages.error(
                    request,
                    "Please fill all batch fields."
                )

            return redirect_to_academic_tab(
                'batches'
            )

        # ----------------------------------------------------
        # BATCH: UPDATE
        # ----------------------------------------------------

        elif action == 'update_batch':
            batch_id = request.POST.get(
                'batch_id'
            )

            department_id = request.POST.get(
                'department'
            )

            batch_name = request.POST.get(
                'batch_name',
                ''
            ).strip()

            admission_year = request.POST.get(
                'admission_year'
            )

            batch = Batch.objects.select_related(
                'department'
            ).filter(
                id=batch_id
            ).first()

            department = None

            if department_id:
                department = Department.objects.filter(
                    id=department_id
                ).first()

            if (
                batch and
                department and
                batch_name and
                admission_year
            ):
                old_repr = (
                    f'{batch.department.code} - '
                    f'{batch.batch_name}'
                )

                batch.department = department
                batch.batch_name = batch_name
                batch.admission_year = admission_year
                batch.save()

                create_audit_log(
                    request,
                    action='UPDATE',
                    module='Academic Setup',
                    description=(
                        f'Updated batch from '
                        f'{old_repr} to '
                        f'{batch.department.code} - '
                        f'{batch.batch_name}'
                    ),
                    target_model='Batch',
                    target_id=batch.id,
                    target_repr=(
                        f'{batch.department.code} - '
                        f'{batch.batch_name}'
                    ),
                )

                messages.success(
                    request,
                    "Batch updated successfully."
                )

            else:
                messages.error(
                    request,
                    "Invalid batch update request."
                )

            return redirect_to_academic_tab(
                'batches'
            )

        # ----------------------------------------------------
        # BATCH: DELETE
        # ----------------------------------------------------

        elif action == 'delete_batch':
            batch_id = request.POST.get(
                'batch_id'
            )

            batch = Batch.objects.select_related(
                'department'
            ).filter(
                id=batch_id
            ).first()

            if batch:
                has_students = StudentProfile.objects.filter(
                    batch=batch
                ).exists()

                has_offerings = CourseOffering.objects.filter(
                    batch=batch
                ).exists()

                if (
                    has_students or
                    has_offerings
                ):
                    messages.error(
                        request,
                        (
                            "Cannot delete this batch because "
                            "it has students or course offerings."
                        )
                    )

                else:
                    batch_id_value = batch.id

                    batch_repr = (
                        f'{batch.department.code} - '
                        f'{batch.batch_name}'
                    )

                    create_audit_log(
                        request,
                        action='DELETE',
                        module='Academic Setup',
                        description=(
                            f'Deleted batch: '
                            f'{batch_repr}'
                        ),
                        target_model='Batch',
                        target_id=batch_id_value,
                        target_repr=batch_repr,
                    )

                    batch.delete()

                    messages.success(
                        request,
                        "Batch deleted successfully."
                    )

            else:
                messages.error(
                    request,
                    "Batch not found."
                )

            return redirect_to_academic_tab(
                'batches'
            )

        # ----------------------------------------------------
        # SEMESTER: CREATE
        # ----------------------------------------------------

        elif action == 'create_semester':
            name = request.POST.get(
                'name',
                ''
            ).strip()

            number = request.POST.get(
                'number'
            )

            if name and number:
                semester, created = Semester.objects.get_or_create(
                    number=number,
                    defaults={
                        'name': name
                    }
                )

                if created:
                    create_audit_log(
                        request,
                        action='CREATE',
                        module='Academic Setup',
                        description=(
                            f'Created semester: '
                            f'{semester.name}'
                        ),
                        target_model='Semester',
                        target_id=semester.id,
                        target_repr=semester.name,
                    )

                    messages.success(
                        request,
                        "Semester created successfully."
                    )

                else:
                    messages.warning(
                        request,
                        "Semester already exists."
                    )

            else:
                messages.error(
                    request,
                    "Please enter semester name and number."
                )

            return redirect_to_academic_tab(
                'semesters'
            )

        # ----------------------------------------------------
        # SEMESTER: UPDATE
        # ----------------------------------------------------

        elif action == 'update_semester':
            semester_id = request.POST.get(
                'semester_id'
            )

            name = request.POST.get(
                'name',
                ''
            ).strip()

            number = request.POST.get(
                'number'
            )

            semester = Semester.objects.filter(
                id=semester_id
            ).first()

            if semester and name and number:
                duplicate = Semester.objects.exclude(
                    id=semester.id
                ).filter(
                    number=number
                ).exists()

                if duplicate:
                    messages.error(
                        request,
                        (
                            "Another semester already uses "
                            "this number."
                        )
                    )

                else:
                    old_repr = (
                        f'{semester.number} - '
                        f'{semester.name}'
                    )

                    semester.name = name
                    semester.number = number
                    semester.save()

                    create_audit_log(
                        request,
                        action='UPDATE',
                        module='Academic Setup',
                        description=(
                            f'Updated semester from '
                            f'{old_repr} to '
                            f'{semester.number} - '
                            f'{semester.name}'
                        ),
                        target_model='Semester',
                        target_id=semester.id,
                        target_repr=(
                            f'{semester.number} - '
                            f'{semester.name}'
                        ),
                    )

                    messages.success(
                        request,
                        "Semester updated successfully."
                    )

            else:
                messages.error(
                    request,
                    "Invalid semester update request."
                )

            return redirect_to_academic_tab(
                'semesters'
            )

        # ----------------------------------------------------
        # SEMESTER: DELETE
        # ----------------------------------------------------

        elif action == 'delete_semester':
            semester_id = request.POST.get(
                'semester_id'
            )

            semester = Semester.objects.filter(
                id=semester_id
            ).first()

            if semester:
                has_courses = Course.objects.filter(
                    semester=semester
                ).exists()

                has_offerings = CourseOffering.objects.filter(
                    semester=semester
                ).exists()

                has_students = StudentProfile.objects.filter(
                    current_semester=semester
                ).exists()

                if (
                    has_courses or
                    has_offerings or
                    has_students
                ):
                    messages.error(
                        request,
                        (
                            "Cannot delete this semester because "
                            "it is used by courses, offerings, "
                            "or students."
                        )
                    )

                else:
                    semester_id_value = semester.id

                    semester_repr = (
                        f'{semester.number} - '
                        f'{semester.name}'
                    )

                    create_audit_log(
                        request,
                        action='DELETE',
                        module='Academic Setup',
                        description=(
                            f'Deleted semester: '
                            f'{semester_repr}'
                        ),
                        target_model='Semester',
                        target_id=semester_id_value,
                        target_repr=semester_repr,
                    )

                    semester.delete()

                    messages.success(
                        request,
                        "Semester deleted successfully."
                    )

            else:
                messages.error(
                    request,
                    "Semester not found."
                )

            return redirect_to_academic_tab(
                'semesters'
            )

        # ----------------------------------------------------
        # COURSE: CREATE
        # ----------------------------------------------------

        elif action == 'create_course':
            department_id = request.POST.get(
                'department'
            )

            code = request.POST.get(
                'code',
                ''
            ).strip()

            title = request.POST.get(
                'title',
                ''
            ).strip()

            credit = request.POST.get(
                'credit'
            )

            semester_id = request.POST.get(
                'semester'
            )

            department = None
            semester = None

            if department_id:
                department = Department.objects.filter(
                    id=department_id
                ).first()

            if semester_id:
                semester = Semester.objects.filter(
                    id=semester_id
                ).first()

            if (
                department and
                code and
                title and
                credit and
                semester
            ):
                course, created = Course.objects.get_or_create(
                    code=code.upper(),
                    defaults={
                        'department': department,
                        'title': title,
                        'credit': credit,
                        'semester': semester,
                    }
                )

                if created:
                    create_audit_log(
                        request,
                        action='CREATE',
                        module='Academic Setup',
                        description=(
                            f'Created course: '
                            f'{course.code} - '
                            f'{course.title}'
                        ),
                        target_model='Course',
                        target_id=course.id,
                        target_repr=(
                            f'{course.code} - '
                            f'{course.title}'
                        ),
                    )

                    messages.success(
                        request,
                        "Course created successfully."
                    )

                else:
                    messages.warning(
                        request,
                        "Course already exists."
                    )

            else:
                messages.error(
                    request,
                    "Please fill all course fields."
                )

            return redirect_to_academic_tab(
                'courses'
            )

        # ----------------------------------------------------
        # COURSE: UPDATE
        # ----------------------------------------------------

        elif action == 'update_course':
            course_id = request.POST.get(
                'course_id'
            )

            department_id = request.POST.get(
                'department'
            )

            code = request.POST.get(
                'code',
                ''
            ).strip()

            title = request.POST.get(
                'title',
                ''
            ).strip()

            credit = request.POST.get(
                'credit'
            )

            semester_id = request.POST.get(
                'semester'
            )

            course = Course.objects.select_related(
                'department',
                'semester'
            ).filter(
                id=course_id
            ).first()

            department = None
            semester = None

            if department_id:
                department = Department.objects.filter(
                    id=department_id
                ).first()

            if semester_id:
                semester = Semester.objects.filter(
                    id=semester_id
                ).first()

            if (
                course and
                department and
                code and
                title and
                credit and
                semester
            ):
                code = code.upper()

                duplicate = Course.objects.exclude(
                    id=course.id
                ).filter(
                    code=code
                ).exists()

                if duplicate:
                    messages.error(
                        request,
                        (
                            "Another course already uses "
                            "this course code."
                        )
                    )

                else:
                    old_repr = (
                        f'{course.code} - '
                        f'{course.title}'
                    )

                    course.department = department
                    course.code = code
                    course.title = title
                    course.credit = credit
                    course.semester = semester
                    course.save()

                    create_audit_log(
                        request,
                        action='UPDATE',
                        module='Academic Setup',
                        description=(
                            f'Updated course from '
                            f'{old_repr} to '
                            f'{course.code} - '
                            f'{course.title}'
                        ),
                        target_model='Course',
                        target_id=course.id,
                        target_repr=(
                            f'{course.code} - '
                            f'{course.title}'
                        ),
                    )

                    messages.success(
                        request,
                        "Course updated successfully."
                    )

            else:
                messages.error(
                    request,
                    "Invalid course update request."
                )

            return redirect_to_academic_tab(
                'courses'
            )

        # ----------------------------------------------------
        # COURSE: DELETE
        # ----------------------------------------------------

        elif action == 'delete_course':
            course_id = request.POST.get(
                'course_id'
            )

            course = Course.objects.filter(
                id=course_id
            ).first()

            if course:
                has_offerings = CourseOffering.objects.filter(
                    course=course
                ).exists()

                if has_offerings:
                    messages.error(
                        request,
                        (
                            "Cannot delete this course because "
                            "it has course offerings."
                        )
                    )

                else:
                    course_id_value = course.id

                    course_repr = (
                        f'{course.code} - '
                        f'{course.title}'
                    )

                    create_audit_log(
                        request,
                        action='DELETE',
                        module='Academic Setup',
                        description=(
                            f'Deleted course: '
                            f'{course_repr}'
                        ),
                        target_model='Course',
                        target_id=course_id_value,
                        target_repr=course_repr,
                    )

                    course.delete()

                    messages.success(
                        request,
                        "Course deleted successfully."
                    )

            else:
                messages.error(
                    request,
                    "Course not found."
                )

            return redirect_to_academic_tab(
                'courses'
            )

        # ----------------------------------------------------
        # COURSE OFFERING: CREATE
        # ----------------------------------------------------

        elif action == 'create_course_offering':
            course_id = request.POST.get(
                'course'
            )

            faculty_id = request.POST.get(
                'faculty'
            )

            batch_id = request.POST.get(
                'batch'
            )

            semester_id = request.POST.get(
                'semester'
            )

            section = request.POST.get(
                'section',
                ''
            ).strip() or 'A'

            is_active = (
                request.POST.get('is_active') == 'on'
            )

            course = None
            batch = None
            semester = None
            faculty = None

            if course_id:
                course = Course.objects.filter(
                    id=course_id
                ).first()

            if batch_id:
                batch = Batch.objects.filter(
                    id=batch_id
                ).first()

            if semester_id:
                semester = Semester.objects.filter(
                    id=semester_id
                ).first()

            if faculty_id:
                faculty = User.objects.filter(
                    id=faculty_id,
                    role='faculty'
                ).first()

            if (
                course and
                batch and
                semester
            ):
                offering = CourseOffering.objects.create(
                    course=course,
                    faculty=faculty,
                    batch=batch,
                    semester=semester,
                    section=section,
                    is_active=is_active
                )

                create_audit_log(
                    request,
                    action='CREATE',
                    module='Academic Setup',
                    description=(
                        f'Created course offering: '
                        f'{offering.course.code} - '
                        f'{offering.batch} - '
                        f'Section {offering.section}'
                    ),
                    target_model='CourseOffering',
                    target_id=offering.id,
                    target_repr=(
                        f'{offering.course.code} - '
                        f'{offering.batch} - '
                        f'Section {offering.section}'
                    ),
                )

                messages.success(
                    request,
                    "Course offering created successfully."
                )

            else:
                messages.error(
                    request,
                    (
                        "Please select course, batch, "
                        "and semester."
                    )
                )

            return redirect_to_academic_tab(
                'offerings'
            )

        # ----------------------------------------------------
        # COURSE OFFERING: UPDATE
        # ----------------------------------------------------

        elif action == 'update_course_offering':
            offering_id = request.POST.get(
                'offering_id'
            )

            course_id = request.POST.get(
                'course'
            )

            faculty_id = request.POST.get(
                'faculty'
            )

            batch_id = request.POST.get(
                'batch'
            )

            semester_id = request.POST.get(
                'semester'
            )

            section = request.POST.get(
                'section',
                ''
            ).strip() or 'A'

            is_active = (
                request.POST.get('is_active') == 'on'
            )

            offering = CourseOffering.objects.select_related(
                'course',
                'batch'
            ).filter(
                id=offering_id
            ).first()

            course = None
            batch = None
            semester = None
            faculty = None

            if course_id:
                course = Course.objects.filter(
                    id=course_id
                ).first()

            if batch_id:
                batch = Batch.objects.filter(
                    id=batch_id
                ).first()

            if semester_id:
                semester = Semester.objects.filter(
                    id=semester_id
                ).first()

            if faculty_id:
                faculty = User.objects.filter(
                    id=faculty_id,
                    role='faculty'
                ).first()

            if (
                offering and
                course and
                batch and
                semester
            ):
                old_repr = (
                    f'{offering.course.code} - '
                    f'{offering.batch} - '
                    f'Section {offering.section}'
                )

                offering.course = course
                offering.faculty = faculty
                offering.batch = batch
                offering.semester = semester
                offering.section = section
                offering.is_active = is_active
                offering.save()

                create_audit_log(
                    request,
                    action='UPDATE',
                    module='Academic Setup',
                    description=(
                        f'Updated course offering from '
                        f'{old_repr} to '
                        f'{offering.course.code} - '
                        f'{offering.batch} - '
                        f'Section {offering.section}'
                    ),
                    target_model='CourseOffering',
                    target_id=offering.id,
                    target_repr=(
                        f'{offering.course.code} - '
                        f'{offering.batch} - '
                        f'Section {offering.section}'
                    ),
                )

                messages.success(
                    request,
                    "Course offering updated successfully."
                )

            else:
                messages.error(
                    request,
                    "Invalid course offering update request."
                )

            return redirect_to_academic_tab(
                'offerings'
            )

        # ----------------------------------------------------
        # COURSE OFFERING: DELETE
        # ----------------------------------------------------

        elif action == 'delete_course_offering':
            offering_id = request.POST.get(
                'offering_id'
            )

            offering = CourseOffering.objects.select_related(
                'course',
                'batch'
            ).filter(
                id=offering_id
            ).first()

            if offering:
                has_registration = (
                    CourseRegistration.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_materials = (
                    CourseMaterial.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_attendance = (
                    AttendanceSession.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_marks = (
                    Mark.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_assignments = (
                    Assignment.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_routine = (
                    ExamRoutine.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                has_seat_plan = (
                    SeatPlan.objects.filter(
                        course_offering=offering
                    ).exists()
                )

                if (
                    has_registration or
                    has_materials or
                    has_attendance or
                    has_marks or
                    has_assignments or
                    has_routine or
                    has_seat_plan
                ):
                    messages.error(
                        request,
                        (
                            "Cannot delete this course offering "
                            "because it is already used by students, "
                            "faculty, exams, or materials."
                        )
                    )

                else:
                    offering_id_value = offering.id

                    offering_repr = (
                        f'{offering.course.code} - '
                        f'{offering.batch} - '
                        f'Section {offering.section}'
                    )

                    create_audit_log(
                        request,
                        action='DELETE',
                        module='Academic Setup',
                        description=(
                            f'Deleted course offering: '
                            f'{offering_repr}'
                        ),
                        target_model='CourseOffering',
                        target_id=offering_id_value,
                        target_repr=offering_repr,
                    )

                    offering.delete()

                    messages.success(
                        request,
                        (
                            "Course offering deleted "
                            "successfully."
                        )
                    )

            else:
                messages.error(
                    request,
                    "Course offering not found."
                )

            return redirect_to_academic_tab(
                'offerings'
            )

        # ----------------------------------------------------
        # UNKNOWN POST ACTION
        # ----------------------------------------------------

        messages.error(
            request,
            "Unknown academic setup action."
        )

        return redirect_to_academic_tab(
            active_tab
        )

    # ========================================================
    # BASE DATA FOR DROPDOWNS
    # ========================================================

    departments = Department.objects.all().order_by(
        'code'
    )

    semesters = Semester.objects.all().order_by(
        'number'
    )

    faculty_users = User.objects.filter(
        role='faculty',
        is_active=True
    ).order_by(
        'first_name',
        'last_name',
        'username'
    )

    # Full unpaginated datasets used by create/edit dropdowns.
    all_batches = Batch.objects.select_related(
        'department'
    ).order_by(
        'department__code',
        'batch_name',
        'admission_year'
    )

    all_courses = Course.objects.select_related(
        'department',
        'semester'
    ).order_by(
        'department__code',
        'code'
    )

    # ========================================================
    # TOTAL COUNTS FOR SUMMARY CARDS
    # ========================================================

    total_department_count = Department.objects.count()
    total_batch_count = Batch.objects.count()
    total_semester_count = Semester.objects.count()
    total_course_count = Course.objects.count()
    total_course_offering_count = (
        CourseOffering.objects.count()
    )

    # ========================================================
    # DEPARTMENT DATA
    # ========================================================

    department_search = request.GET.get(
        'department_search',
        ''
    ).strip()

    departments_queryset = Department.objects.all()

    if department_search:
        departments_queryset = (
            departments_queryset.filter(
                Q(
                    code__icontains=department_search
                ) |
                Q(
                    name__icontains=department_search
                )
            )
        )

    departments_queryset = departments_queryset.order_by(
        'code'
    )

    department_count = departments_queryset.count()

    # ========================================================
    # BATCH FILTERS
    # ========================================================

    batch_search = request.GET.get(
        'batch_search',
        ''
    ).strip()

    batch_department_id = request.GET.get(
        'batch_department',
        ''
    ).strip()

    batch_year = request.GET.get(
        'batch_year',
        ''
    ).strip()

    batch_page_number = request.GET.get(
        'batch_page',
        '1'
    )

    batches_queryset = Batch.objects.select_related(
        'department'
    )

    if batch_search:
        batch_query = (
            Q(
                batch_name__icontains=batch_search
            ) |
            Q(
                department__code__icontains=batch_search
            ) |
            Q(
                department__name__icontains=batch_search
            )
        )

        if batch_search.isdigit():
            batch_query |= Q(
                admission_year=int(batch_search)
            )

        batches_queryset = batches_queryset.filter(
            batch_query
        )

    if batch_department_id:
        batches_queryset = batches_queryset.filter(
            department_id=batch_department_id
        )

    if batch_year:
        batches_queryset = batches_queryset.filter(
            admission_year=batch_year
        )

    batches_queryset = batches_queryset.order_by(
        'department__code',
        '-admission_year',
        'batch_name'
    )

    batch_count = batches_queryset.count()

    batch_paginator = Paginator(
        batches_queryset,
        25
    )

    batch_page_obj = batch_paginator.get_page(
        batch_page_number
    )

    batches = batch_page_obj.object_list

    # ========================================================
    # COURSE FILTERS
    # ========================================================

    course_search = request.GET.get(
        'course_search',
        ''
    ).strip()

    course_department_id = request.GET.get(
        'course_department',
        ''
    ).strip()

    course_semester_id = request.GET.get(
        'course_semester',
        ''
    ).strip()

    course_page_number = request.GET.get(
        'course_page',
        '1'
    )

    courses_queryset = Course.objects.select_related(
        'department',
        'semester'
    )

    if course_search:
        courses_queryset = courses_queryset.filter(
            Q(
                code__icontains=course_search
            ) |
            Q(
                title__icontains=course_search
            ) |
            Q(
                department__code__icontains=course_search
            ) |
            Q(
                department__name__icontains=course_search
            ) |
            Q(
                semester__name__icontains=course_search
            )
        )

    if course_department_id:
        courses_queryset = courses_queryset.filter(
            department_id=course_department_id
        )

    if course_semester_id:
        courses_queryset = courses_queryset.filter(
            semester_id=course_semester_id
        )

    courses_queryset = courses_queryset.order_by(
        'department__code',
        'semester__number',
        'code'
    )

    course_count = courses_queryset.count()

    course_paginator = Paginator(
        courses_queryset,
        25
    )

    course_page_obj = course_paginator.get_page(
        course_page_number
    )

    courses = course_page_obj.object_list

    # ========================================================
    # COURSE OFFERING FILTERS
    # ========================================================

    offering_search = request.GET.get(
        'offering_search',
        ''
    ).strip()

    offering_department_id = request.GET.get(
        'offering_department',
        ''
    ).strip()

    offering_batch_id = request.GET.get(
        'offering_batch',
        ''
    ).strip()

    offering_semester_id = request.GET.get(
        'offering_semester',
        ''
    ).strip()

    offering_faculty_id = request.GET.get(
        'offering_faculty',
        ''
    ).strip()

    offering_status = request.GET.get(
        'offering_status',
        ''
    ).strip()

    offering_page_number = request.GET.get(
        'offering_page',
        '1'
    )

    course_offerings_queryset = (
        CourseOffering.objects.select_related(
            'course',
            'course__department',
            'faculty',
            'batch',
            'batch__department',
            'semester'
        )
    )

    if offering_search:
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                Q(
                    course__code__icontains=offering_search
                ) |
                Q(
                    course__title__icontains=offering_search
                ) |
                Q(
                    batch__batch_name__icontains=offering_search
                ) |
                Q(
                    batch__department__code__icontains=offering_search
                ) |
                Q(
                    section__icontains=offering_search
                ) |
                Q(
                    faculty__username__icontains=offering_search
                ) |
                Q(
                    faculty__first_name__icontains=offering_search
                ) |
                Q(
                    faculty__last_name__icontains=offering_search
                )
            )
        )

    if offering_department_id:
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                Q(
                    course__department_id=offering_department_id
                ) |
                Q(
                    batch__department_id=offering_department_id
                )
            )
        )

    if offering_batch_id:
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                batch_id=offering_batch_id
            )
        )

    if offering_semester_id:
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                semester_id=offering_semester_id
            )
        )

    if offering_faculty_id:
        if offering_faculty_id == 'unassigned':
            course_offerings_queryset = (
                course_offerings_queryset.filter(
                    faculty__isnull=True
                )
            )

        else:
            course_offerings_queryset = (
                course_offerings_queryset.filter(
                    faculty_id=offering_faculty_id
                )
            )

    if offering_status == 'active':
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                is_active=True
            )
        )

    elif offering_status == 'inactive':
        course_offerings_queryset = (
            course_offerings_queryset.filter(
                is_active=False
            )
        )

    course_offerings_queryset = (
        course_offerings_queryset.order_by(
            'course__department__code',
            'semester__number',
            'course__code',
            'batch__batch_name',
            'section'
        )
    )

    course_offering_count = (
        course_offerings_queryset.count()
    )

    offering_paginator = Paginator(
        course_offerings_queryset,
        30
    )

    offering_page_obj = offering_paginator.get_page(
        offering_page_number
    )

    course_offerings = (
        offering_page_obj.object_list
    )

    # ========================================================
    # PAGINATION QUERY STRINGS
    # ========================================================

    department_query_string = (
        build_query_string_without()
    )

    batch_query_string = (
        build_query_string_without(
            'batch_page'
        )
    )

    course_query_string = (
        build_query_string_without(
            'course_page'
        )
    )

    offering_query_string = (
        build_query_string_without(
            'offering_page'
        )
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {
        # -----------------------------------------------
        # Active tab
        # -----------------------------------------------
        'active_tab':
            active_tab,

        # -----------------------------------------------
        # Summary totals
        # -----------------------------------------------
        'total_department_count':
            total_department_count,

        'total_batch_count':
            total_batch_count,

        'total_semester_count':
            total_semester_count,

        'total_course_count':
            total_course_count,

        'total_course_offering_count':
            total_course_offering_count,

        # -----------------------------------------------
        # Department data
        # -----------------------------------------------
        'departments':
            departments,

        'department_records':
            departments_queryset,

        'department_count':
            department_count,

        'department_search':
            department_search,

        # -----------------------------------------------
        # Semester data
        # -----------------------------------------------
        'semesters':
            semesters,

        # -----------------------------------------------
        # Full dropdown datasets
        # -----------------------------------------------
        'all_batches':
            all_batches,

        'all_courses':
            all_courses,

        'faculty_users':
            faculty_users,

        # -----------------------------------------------
        # Paginated batches
        # -----------------------------------------------
        'batches':
            batches,

        'batch_page_obj':
            batch_page_obj,

        'batch_paginator':
            batch_paginator,

        'batch_count':
            batch_count,

        'batch_search':
            batch_search,

        'batch_department_id':
            batch_department_id,

        'batch_year':
            batch_year,

        # -----------------------------------------------
        # Paginated courses
        # -----------------------------------------------
        'courses':
            courses,

        'course_page_obj':
            course_page_obj,

        'course_paginator':
            course_paginator,

        'course_count':
            course_count,

        'course_search':
            course_search,

        'course_department_id':
            course_department_id,

        'course_semester_id':
            course_semester_id,

        # -----------------------------------------------
        # Paginated course offerings
        # -----------------------------------------------
        'course_offerings':
            course_offerings,

        'offering_page_obj':
            offering_page_obj,

        'offering_paginator':
            offering_paginator,

        'course_offering_count':
            course_offering_count,

        'offering_search':
            offering_search,

        'offering_department_id':
            offering_department_id,

        'offering_batch_id':
            offering_batch_id,

        'offering_semester_id':
            offering_semester_id,

        'offering_faculty_id':
            offering_faculty_id,

        'offering_status':
            offering_status,

        # -----------------------------------------------
        # Pagination query strings
        # -----------------------------------------------
        'department_query_string':
            department_query_string,

        'batch_query_string':
            batch_query_string,

        'course_query_string':
            course_query_string,

        'offering_query_string':
            offering_query_string,
    }

    return render(
        request,
        'dashboard/academic_setup.html',
        context
    )


# ============================================================
# DEPARTMENT HEAD DASHBOARD
# ============================================================

@login_required
def dept_head_dashboard(request):
    return render(
        request,
        'dashboard/dept_head_dashboard.html'
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):
    return render(
        request,
        'dashboard/admin_dashboard.html'
    )


# ============================================================
# SUPER ADMIN DASHBOARD
# ============================================================

@login_required
def super_admin_dashboard(request):
    return render(
        request,
        'dashboard/super_admin_dashboard.html'
    )