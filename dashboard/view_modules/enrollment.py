from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render

from academics.models import Department, Batch, Semester, CourseOffering
from students.models import StudentProfile, CourseRegistration
from dashboard.view_modules.audit import create_audit_log


@login_required
def course_enrollment(request):
    if request.user.role not in ['super_admin', 'admin', 'dept_head']:
        return redirect('dashboard')

    # =========================================================
    # WORKSPACE FILTERS
    # Used by Bulk Enrollment and Manual Enrollment
    # =========================================================
    selected_department_id = request.GET.get('department', '').strip()
    selected_batch_id = request.GET.get('batch', '').strip()
    selected_semester_id = request.GET.get('semester', '').strip()

    # =========================================================
    # REGISTRATION MANAGEMENT FILTERS
    # Separate from enrollment workspace filters
    # =========================================================
    registration_search = request.GET.get(
        'registration_search',
        ''
    ).strip()

    registration_department_id = request.GET.get(
        'registration_department',
        ''
    ).strip()

    registration_batch_id = request.GET.get(
        'registration_batch',
        ''
    ).strip()

    registration_semester_id = request.GET.get(
        'registration_semester',
        ''
    ).strip()

    registration_status = request.GET.get(
        'registration_status',
        ''
    ).strip()

    active_tab = request.GET.get('tab', 'bulk').strip()

    if active_tab not in ['bulk', 'manual', 'registrations']:
        active_tab = 'bulk'

    # =========================================================
    # REDIRECT HELPER
    # Preserves filters after POST actions
    # =========================================================
    def redirect_with_filters_from_post(default_tab=None):
        params = {}

        department_id = request.POST.get(
            'selected_department_id',
            ''
        ).strip()

        batch_id = request.POST.get(
            'selected_batch_id',
            ''
        ).strip()

        semester_id = request.POST.get(
            'selected_semester_id',
            ''
        ).strip()

        post_tab = request.POST.get(
            'return_tab',
            ''
        ).strip()

        if department_id:
            params['department'] = department_id

        if batch_id:
            params['batch'] = batch_id

        if semester_id:
            params['semester'] = semester_id

        # Preserve registration management filters
        registration_search_post = request.POST.get(
            'registration_search',
            ''
        ).strip()

        registration_department_post = request.POST.get(
            'registration_department',
            ''
        ).strip()

        registration_batch_post = request.POST.get(
            'registration_batch',
            ''
        ).strip()

        registration_semester_post = request.POST.get(
            'registration_semester',
            ''
        ).strip()

        registration_status_post = request.POST.get(
            'registration_status',
            ''
        ).strip()

        registration_page_post = request.POST.get(
            'registration_page',
            ''
        ).strip()

        if registration_search_post:
            params['registration_search'] = (
                registration_search_post
            )

        if registration_department_post:
            params['registration_department'] = (
                registration_department_post
            )

        if registration_batch_post:
            params['registration_batch'] = (
                registration_batch_post
            )

        if registration_semester_post:
            params['registration_semester'] = (
                registration_semester_post
            )

        if registration_status_post:
            params['registration_status'] = (
                registration_status_post
            )

        if registration_page_post:
            params['registration_page'] = (
                registration_page_post
            )

        if post_tab in ['bulk', 'manual', 'registrations']:
            params['tab'] = post_tab
        elif default_tab:
            params['tab'] = default_tab

        query_string = urlencode(params)

        if query_string:
            return redirect(
                f"/course-enrollment/?{query_string}"
            )

        return redirect('course_enrollment')

    # =========================================================
    # POST ACTIONS
    # =========================================================
    if request.method == 'POST':
        action = request.POST.get('action')

        # -----------------------------------------------------
        # MANUAL ENROLLMENT
        # -----------------------------------------------------
        if action == 'enroll_selected':
            student_ids = request.POST.getlist('students')
            course_offering_ids = request.POST.getlist(
                'course_offerings'
            )
            status = (
                request.POST.get('status')
                or 'approved'
            )

            valid_statuses = [
                'pending',
                'approved',
                'rejected',
            ]

            if status not in valid_statuses:
                status = 'approved'

            if not student_ids:
                messages.error(
                    request,
                    "Please select at least one student."
                )
                return redirect_with_filters_from_post(
                    default_tab='manual'
                )

            if not course_offering_ids:
                messages.error(
                    request,
                    "Please select at least one course offering."
                )
                return redirect_with_filters_from_post(
                    default_tab='manual'
                )

            students = StudentProfile.objects.filter(
                id__in=student_ids,
                is_active=True,
                user__is_active=True,
            )

            course_offerings = CourseOffering.objects.filter(
                id__in=course_offering_ids,
                is_active=True,
            )

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for student in students:
                for offering in course_offerings:
                    if student.batch_id != offering.batch_id:
                        skipped_count += 1
                        continue

                    registration, created = (
                        CourseRegistration.objects.update_or_create(
                            student=student,
                            course_offering=offering,
                            defaults={
                                'status': status,
                            },
                        )
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            create_audit_log(
                request,
                action='ENROLL',
                module='Course Enrollment',
                description=(
                    'Manual course enrollment completed. '
                    f'Students selected: {len(student_ids)}, '
                    'Course offerings selected: '
                    f'{len(course_offering_ids)}, '
                    f'Created: {created_count}, '
                    f'Updated: {updated_count}, '
                    f'Skipped: {skipped_count}, '
                    f'Status: {status}.'
                ),
                target_model='CourseRegistration',
                target_id='bulk',
                target_repr='Manual course enrollment',
            )

            messages.success(
                request,
                (
                    'Enrollment completed. '
                    f'Created: {created_count}, '
                    f'Updated: {updated_count}, '
                    f'Skipped: {skipped_count}.'
                )
            )

            return redirect_with_filters_from_post(
                default_tab='manual'
            )

        # -----------------------------------------------------
        # ENTIRE BATCH / SEMESTER ENROLLMENT
        # -----------------------------------------------------
        elif action == 'enroll_entire_semester':
            department_id = request.POST.get(
                'selected_department_id'
            )
            batch_id = request.POST.get(
                'selected_batch_id'
            )
            semester_id = request.POST.get(
                'selected_semester_id'
            )

            course_offering_ids = request.POST.getlist(
                'semester_course_offerings'
            )

            status = (
                request.POST.get('status')
                or 'approved'
            )

            valid_statuses = [
                'pending',
                'approved',
                'rejected',
            ]

            if status not in valid_statuses:
                status = 'approved'

            if not department_id:
                messages.error(
                    request,
                    "Please select a department first."
                )
                return redirect_with_filters_from_post(
                    default_tab='bulk'
                )

            if not batch_id:
                messages.error(
                    request,
                    "Please select a batch first."
                )
                return redirect_with_filters_from_post(
                    default_tab='bulk'
                )

            if not semester_id:
                messages.error(
                    request,
                    "Please select a semester first."
                )
                return redirect_with_filters_from_post(
                    default_tab='bulk'
                )

            if not course_offering_ids:
                messages.error(
                    request,
                    (
                        "Please select at least one course "
                        "offering for bulk enrollment."
                    )
                )
                return redirect_with_filters_from_post(
                    default_tab='bulk'
                )

            semester_students = (
                StudentProfile.objects
                .select_related(
                    'user',
                    'department',
                    'batch',
                    'current_semester',
                )
                .filter(
                    is_active=True,
                    user__is_active=True,
                    department_id=department_id,
                    batch_id=batch_id,
                    current_semester_id=semester_id,
                )
            )

            semester_course_offerings = (
                CourseOffering.objects
                .select_related(
                    'course',
                    'batch',
                    'semester',
                )
                .filter(
                    id__in=course_offering_ids,
                    is_active=True,
                    batch_id=batch_id,
                    semester_id=semester_id,
                )
            )

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for student in semester_students:
                for offering in semester_course_offerings:
                    if student.batch_id != offering.batch_id:
                        skipped_count += 1
                        continue

                    if (
                        student.current_semester_id
                        != offering.semester_id
                    ):
                        skipped_count += 1
                        continue

                    registration, created = (
                        CourseRegistration.objects.update_or_create(
                            student=student,
                            course_offering=offering,
                            defaults={
                                'status': status,
                            },
                        )
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            student_total = semester_students.count()
            offering_total = (
                semester_course_offerings.count()
            )

            create_audit_log(
                request,
                action='BULK_ENROLL_SEMESTER',
                module='Course Enrollment',
                description=(
                    'Entire semester enrollment completed. '
                    f'Department ID: {department_id}, '
                    f'Batch ID: {batch_id}, '
                    f'Semester ID: {semester_id}, '
                    f'Students found: {student_total}, '
                    'Course offerings selected: '
                    f'{offering_total}, '
                    f'Created: {created_count}, '
                    f'Updated: {updated_count}, '
                    f'Skipped: {skipped_count}, '
                    f'Status: {status}.'
                ),
                target_model='CourseRegistration',
                target_id='semester_bulk',
                target_repr=(
                    'Entire semester course enrollment'
                ),
            )

            messages.success(
                request,
                (
                    'Bulk enrollment completed. '
                    f'Students: {student_total}, '
                    f'Created: {created_count}, '
                    f'Updated: {updated_count}, '
                    f'Skipped: {skipped_count}.'
                )
            )

            return redirect_with_filters_from_post(
                default_tab='bulk'
            )

        # -----------------------------------------------------
        # UPDATE REGISTRATION STATUS
        # -----------------------------------------------------
        elif action == 'update_registration':
            registration_id = request.POST.get(
                'registration_id'
            )
            status = request.POST.get('status')

            registration = (
                CourseRegistration.objects
                .select_related(
                    'student',
                    'course_offering',
                    'course_offering__course',
                )
                .filter(
                    id=registration_id
                )
                .first()
            )

            valid_statuses = [
                'pending',
                'approved',
                'rejected',
            ]

            if (
                registration
                and status in valid_statuses
            ):
                registration.status = status
                registration.save(
                    update_fields=['status']
                )

                create_audit_log(
                    request,
                    action='UPDATE',
                    module='Course Enrollment',
                    description=(
                        'Updated registration status to '
                        f'{status} for '
                        f'{registration.student.student_id} - '
                        f'{registration.course_offering.course.code}.'
                    ),
                    target_model='CourseRegistration',
                    target_id=registration.id,
                    target_repr=(
                        f'{registration.student.student_id} - '
                        f'{registration.course_offering.course.code}'
                    ),
                )

                messages.success(
                    request,
                    "Course registration status updated."
                )
            else:
                messages.error(
                    request,
                    "Invalid registration update request."
                )

            return redirect_with_filters_from_post(
                default_tab='registrations'
            )

        # -----------------------------------------------------
        # REMOVE REGISTRATION
        # -----------------------------------------------------
        elif action == 'remove_registration':
            registration_id = request.POST.get(
                'registration_id'
            )

            registration = (
                CourseRegistration.objects
                .select_related(
                    'student',
                    'course_offering',
                    'course_offering__course',
                )
                .filter(
                    id=registration_id
                )
                .first()
            )

            if registration:
                registration_id_value = registration.id

                registration_repr = (
                    f'{registration.student.student_id} - '
                    f'{registration.course_offering.course.code}'
                )

                create_audit_log(
                    request,
                    action='REMOVE',
                    module='Course Enrollment',
                    description=(
                        'Removed course registration: '
                        f'{registration_repr}.'
                    ),
                    target_model='CourseRegistration',
                    target_id=registration_id_value,
                    target_repr=registration_repr,
                )

                registration.delete()

                messages.success(
                    request,
                    "Course registration removed successfully."
                )
            else:
                messages.error(
                    request,
                    "Course registration not found."
                )

            return redirect_with_filters_from_post(
                default_tab='registrations'
            )

    # =========================================================
    # BASE FILTER OPTIONS
    # Keep these complete so dropdown filters always work
    # =========================================================
    all_departments = Department.objects.all().order_by(
        'code'
    )

    all_batches = (
        Batch.objects
        .select_related('department')
        .order_by(
            'department__code',
            'batch_name',
        )
    )

    all_semesters = Semester.objects.all().order_by(
        'number'
    )

    # =========================================================
    # WORKSPACE BATCH OPTIONS
    # Can be narrowed by selected department
    # =========================================================
    batches = all_batches

    if selected_department_id:
        batches = batches.filter(
            department_id=selected_department_id
        )

    # =========================================================
    # MANUAL ENROLLMENT STUDENTS
    # =========================================================
    students = (
        StudentProfile.objects
        .select_related(
            'user',
            'department',
            'batch',
            'current_semester',
        )
        .filter(
            is_active=True,
            user__is_active=True,
        )
    )

    if selected_department_id:
        students = students.filter(
            department_id=selected_department_id
        )

    if selected_batch_id:
        students = students.filter(
            batch_id=selected_batch_id
        )

    if selected_semester_id:
        students = students.filter(
            current_semester_id=selected_semester_id
        )

    students = students.order_by(
        'department__code',
        'batch__batch_name',
        'student_id',
    )

    # =========================================================
    # MANUAL ENROLLMENT COURSE OFFERINGS
    # =========================================================
    course_offerings = (
        CourseOffering.objects
        .select_related(
            'course',
            'course__department',
            'faculty',
            'batch',
            'batch__department',
            'semester',
        )
        .filter(
            is_active=True
        )
    )

    if selected_department_id:
        course_offerings = course_offerings.filter(
            Q(
                course__department_id=
                selected_department_id
            )
            |
            Q(
                batch__department_id=
                selected_department_id
            )
        )

    if selected_batch_id:
        course_offerings = course_offerings.filter(
            batch_id=selected_batch_id
        )

    if selected_semester_id:
        course_offerings = course_offerings.filter(
            semester_id=selected_semester_id
        )

    course_offerings = course_offerings.order_by(
        'batch__department__code',
        'batch__batch_name',
        'semester__number',
        'course__code',
        'section',
    )

    # =========================================================
    # BULK ENROLLMENT TARGET STUDENTS
    # =========================================================
    semester_students = (
        StudentProfile.objects
        .select_related(
            'user',
            'department',
            'batch',
            'current_semester',
        )
        .filter(
            is_active=True,
            user__is_active=True,
        )
    )

    if selected_department_id:
        semester_students = semester_students.filter(
            department_id=selected_department_id
        )

    if selected_batch_id:
        semester_students = semester_students.filter(
            batch_id=selected_batch_id
        )

    if selected_semester_id:
        semester_students = semester_students.filter(
            current_semester_id=selected_semester_id
        )

    semester_students = semester_students.order_by(
        'department__code',
        'batch__batch_name',
        'student_id',
    )

    # =========================================================
    # BULK ENROLLMENT TARGET OFFERINGS
    # =========================================================
    semester_course_offerings = (
        CourseOffering.objects
        .select_related(
            'course',
            'course__department',
            'faculty',
            'batch',
            'batch__department',
            'semester',
        )
        .filter(
            is_active=True
        )
    )

    if selected_department_id:
        semester_course_offerings = (
            semester_course_offerings.filter(
                Q(
                    course__department_id=
                    selected_department_id
                )
                |
                Q(
                    batch__department_id=
                    selected_department_id
                )
            )
        )

    if selected_batch_id:
        semester_course_offerings = (
            semester_course_offerings.filter(
                batch_id=selected_batch_id
            )
        )

    if selected_semester_id:
        semester_course_offerings = (
            semester_course_offerings.filter(
                semester_id=selected_semester_id
            )
        )

    semester_course_offerings = (
        semester_course_offerings.order_by(
            'batch__department__code',
            'batch__batch_name',
            'semester__number',
            'course__code',
            'section',
        )
    )

    # =========================================================
    # SERVER-SIDE REGISTRATION MANAGEMENT
    # =========================================================
    registrations = (
        CourseRegistration.objects
        .select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester',
            'course_offering',
            'course_offering__course',
            'course_offering__course__department',
            'course_offering__batch',
            'course_offering__batch__department',
            'course_offering__semester',
            'course_offering__faculty',
        )
    )

    # Search across student and course information
    if registration_search:
        registrations = registrations.filter(
            Q(
                student__student_id__icontains=
                registration_search
            )
            |
            Q(
                student__user__username__icontains=
                registration_search
            )
            |
            Q(
                student__user__first_name__icontains=
                registration_search
            )
            |
            Q(
                student__user__last_name__icontains=
                registration_search
            )
            |
            Q(
                course_offering__course__code__icontains=
                registration_search
            )
            |
            Q(
                course_offering__course__title__icontains=
                registration_search
            )
        )

    if registration_department_id:
        registrations = registrations.filter(
            Q(
                student__department_id=
                registration_department_id
            )
            |
            Q(
                course_offering__course__department_id=
                registration_department_id
            )
            |
            Q(
                course_offering__batch__department_id=
                registration_department_id
            )
        )

    if registration_batch_id:
        registrations = registrations.filter(
            course_offering__batch_id=
            registration_batch_id
        )

    if registration_semester_id:
        registrations = registrations.filter(
            course_offering__semester_id=
            registration_semester_id
        )

    valid_registration_statuses = [
        'pending',
        'approved',
        'rejected',
    ]

    if (
        registration_status
        in valid_registration_statuses
    ):
        registrations = registrations.filter(
            status=registration_status
        )

    registrations = registrations.order_by(
        'student__student_id',
        'course_offering__course__code',
        'course_offering__section',
    )

    # Count AFTER server-side filtering
    registration_count = registrations.count()

    # True server-side pagination
    paginator = Paginator(
        registrations,
        25
    )

    registration_page_number = request.GET.get(
        'registration_page'
    )

    registration_page_obj = paginator.get_page(
        registration_page_number
    )

    # =========================================================
    # PRESERVED QUERY STRING FOR PAGINATION
    # Excludes the page number itself
    # =========================================================
    pagination_params = request.GET.copy()

    if 'registration_page' in pagination_params:
        pagination_params.pop(
            'registration_page'
        )

    registration_query_string = (
        pagination_params.urlencode()
    )

    # =========================================================
    # CONTEXT
    # =========================================================
    context = {
        # Complete dropdown sources
        'departments': all_departments,
        'batches': batches,
        'all_batches': all_batches,
        'semesters': all_semesters,

        # Enrollment workspaces
        'students': students,
        'course_offerings': course_offerings,

        'semester_students': semester_students,
        'semester_course_offerings':
            semester_course_offerings,

        # Workspace filters
        'selected_department_id':
            selected_department_id,
        'selected_batch_id':
            selected_batch_id,
        'selected_semester_id':
            selected_semester_id,

        # Workspace counts
        'student_count': students.count(),
        'course_offering_count':
            course_offerings.count(),

        'semester_student_count':
            semester_students.count(),

        'semester_course_offering_count':
            semester_course_offerings.count(),

        # Registration management
        'registrations':
            registration_page_obj.object_list,

        'registration_page_obj':
            registration_page_obj,

        'registration_paginator':
            paginator,

        'registration_count':
            registration_count,

        'registration_query_string':
            registration_query_string,

        # Registration filter values
        'registration_search':
            registration_search,

        'registration_department_id':
            registration_department_id,

        'registration_batch_id':
            registration_batch_id,

        'registration_semester_id':
            registration_semester_id,

        'registration_status':
            registration_status,

        # Active workspace tab
        'active_tab':
            active_tab,
    }

    return render(
        request,
        'dashboard/course_enrollment.html',
        context,
    )
