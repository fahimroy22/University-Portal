from decimal import Decimal
from typing import final
from urllib import request

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from academics.models import CourseOffering, CourseMaterial
from students.models import CourseRegistration
from faculty.models import (
    AttendanceSession,
    AttendanceRecord,
    Mark,
    Assignment,
    AssignmentSubmission,
)
from applications.models import StudentApplication
from exams.models import (
    HallDuty,
    ExamRoutine,
    ResultPublication,
    StudentMarkReviewRequest,
    ResultCorrectionRequest,
)
from dashboard.view_modules.notices import get_notices_for_user


@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    today = timezone.localdate()
    now = timezone.now()

    assigned_courses = CourseOffering.objects.filter(
        faculty=request.user,
        is_active=True
    ).select_related(
        'course',
        'batch',
        'semester'
    ).order_by(
        'semester__number',
        'course__code'
    )

    course_cards = []

    for offering in assigned_courses:
        total_students = CourseRegistration.objects.filter(
            course_offering=offering,
            status='approved'
        ).count()

        total_classes = AttendanceSession.objects.filter(
            course_offering=offering
        ).count()

        total_assignments = Assignment.objects.filter(
            course_offering=offering
        ).count()

        marks_submitted = Mark.objects.filter(
            course_offering=offering,
            is_submitted=True
        ).count()

        course_cards.append({
            'offering': offering,
            'total_students': total_students,
            'total_classes': total_classes,
            'total_assignments': total_assignments,
            'marks_submitted': marks_submitted,
        })

    hall_duties = HallDuty.objects.filter(
        faculty=request.user
    ).select_related(
        'exam_routine',
        'exam_routine__course_offering',
        'exam_routine__course_offering__course',
        'exam_routine__course_offering__batch',
        'exam_routine__course_offering__semester'
    ).order_by(
        'exam_routine__exam_date',
        'exam_routine__start_time'
    )

    upcoming_hall_duties = hall_duties.filter(
        exam_routine__exam_date__gte=today
    )[:5]

    upcoming_exams = ExamRoutine.objects.filter(
        course_offering__faculty=request.user,
        is_published=True,
        exam_date__gte=today
    ).select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__batch',
        'course_offering__semester'
    ).order_by(
        'exam_date',
        'start_time'
    )[:5]

    upcoming_assignments = Assignment.objects.filter(
        course_offering__faculty=request.user,
        deadline__gte=now,
        is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__batch',
        'course_offering__semester'
    ).order_by(
        'deadline'
    )[:5]

    upcoming_classes = AttendanceSession.objects.filter(
        course_offering__faculty=request.user,
        date__gte=today
    ).select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__batch',
        'course_offering__semester'
    ).order_by(
        'date',
        'id'
    )[:5]

    applications_count = StudentApplication.objects.filter(
        to_user=request.user
    ).count()

    latest_notices = get_notices_for_user(request.user)[:3]

    context = {
        'assigned_courses': assigned_courses,
        'course_cards': course_cards,

        'hall_duties': hall_duties,
        'upcoming_hall_duties': upcoming_hall_duties,
        'upcoming_exams': upcoming_exams,
        'upcoming_assignments': upcoming_assignments,
        'upcoming_classes': upcoming_classes,

        'total_courses': assigned_courses.count(),
        'total_hall_duties': hall_duties.count(),
        'applications_count': applications_count,
        'latest_notices': latest_notices,
    }

    return render(request, 'dashboard/faculty_dashboard.html', context)


@login_required
def faculty_course_action_page(request, action):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    from django.urls import reverse

    action_map = {
        'students': {
            'title': 'Course Students',
            'subtitle': 'Choose an assigned course to view enrolled students and class records.',
            'button_text': 'Open Students',
            'url_name': 'faculty_course_students',
        },
        'attendance': {
            'title': 'Take Attendance',
            'subtitle': 'Choose an assigned course to add class dates and take attendance.',
            'button_text': 'Take Attendance',
            'url_name': 'take_attendance',
        },
        'marks': {
            'title': 'Marks Entry',
            'subtitle': 'Choose an assigned course to enter quiz, assignment, attendance, midterm, and final marks.',
            'button_text': 'Enter Marks',
            'url_name': 'enter_marks',
        },
        'materials': {
            'title': 'Course Materials',
            'subtitle': 'Choose an assigned course to upload and manage study materials.',
            'button_text': 'Manage Materials',
            'url_name': 'course_materials',
        },
        'assignments': {
            'title': 'Assignments',
            'subtitle': 'Choose an assigned course to create assignments and check submissions.',
            'button_text': 'Manage Assignments',
            'url_name': 'faculty_assignments',
        },
        'reports': {
            'title': 'Course Reports',
            'subtitle': 'Choose an assigned course to view attendance, marks, assignment, and performance reports.',
            'button_text': 'Open Report',
            'url_name': 'faculty_course_report',
        },
    }

    action_data = action_map.get(action)

    if not action_data:
        messages.error(request, "Invalid faculty action.")
        return redirect('faculty_dashboard')

    assigned_courses = CourseOffering.objects.filter(
        faculty=request.user,
        is_active=True
    ).select_related(
        'course',
        'batch',
        'semester'
    ).order_by(
        'semester__number',
        'course__code'
    )

    course_cards = []

    for offering in assigned_courses:
        total_students = CourseRegistration.objects.filter(
            course_offering=offering,
            status='approved'
        ).count()

        total_classes = AttendanceSession.objects.filter(
            course_offering=offering
        ).count()

        total_assignments = Assignment.objects.filter(
            course_offering=offering
        ).count()

        marks_submitted = Mark.objects.filter(
            course_offering=offering,
            is_submitted=True
        ).count()

        course_cards.append({
            'offering': offering,
            'total_students': total_students,
            'total_classes': total_classes,
            'total_assignments': total_assignments,
            'marks_submitted': marks_submitted,
            'target_url': reverse(action_data['url_name'], args=[offering.id]),
        })

    context = {
        'action': action,
        'action_data': action_data,
        'course_cards': course_cards,
        'total_courses': assigned_courses.count(),
    }

    return render(request, 'dashboard/faculty_course_action.html', context)
@login_required
def faculty_course_students(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering,
        id=offering_id,
        faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    )

    attendance_sessions = AttendanceSession.objects.filter(
        course_offering=course_offering
    ).order_by('-date', '-id')

    context = {
        'course_offering': course_offering,
        'registrations': registrations,
        'attendance_sessions': attendance_sessions,
    }

    return render(request, 'dashboard/faculty_course_students.html', context)


@login_required
def take_attendance(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering.objects.select_related(
            'course',
            'batch',
            'semester'
        ),
        id=offering_id,
        faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    ).order_by('student__student_id')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_class':
            attendance_date = request.POST.get('attendance_date')
            topic = request.POST.get('topic')

            if attendance_date:
                session = AttendanceSession.objects.create(
                    course_offering=course_offering,
                    date=attendance_date,
                    topic=topic
                )

                for reg in registrations:
                    AttendanceRecord.objects.create(
                        session=session,
                        student=reg.student,
                        is_present=False
                    )

                messages.success(request, "New class date added successfully.")
            else:
                messages.error(request, "Please select a class date.")

            return redirect('take_attendance', offering_id=course_offering.id)

        elif action == 'save_attendance':
            sessions = AttendanceSession.objects.filter(
                course_offering=course_offering
            ).order_by('date', 'id')

            for reg in registrations:
                student = reg.student

                for session in sessions:
                    checkbox_name = f'present_{student.id}_{session.id}'
                    is_present = request.POST.get(checkbox_name) == 'on'

                    record, created = AttendanceRecord.objects.get_or_create(
                        session=session,
                        student=student,
                        defaults={
                            'is_present': is_present
                        }
                    )

                    if not created:
                        record.is_present = is_present
                        record.save()

            messages.success(request, "Attendance register saved successfully.")
            return redirect('take_attendance', offering_id=course_offering.id)

    sessions = AttendanceSession.objects.filter(
        course_offering=course_offering
    ).order_by('date', 'id')

    records = AttendanceRecord.objects.filter(
        session__course_offering=course_offering
    ).select_related(
        'session',
        'student'
    )

    attendance_lookup = {
        (record.student_id, record.session_id): record.is_present
        for record in records
    }

    midterm_routine = ExamRoutine.objects.filter(
        course_offering=course_offering,
        exam_type='midterm',
        is_published=True
    ).first()

    final_routine = ExamRoutine.objects.filter(
        course_offering=course_offering,
        exam_type='final',
        is_published=True
    ).first()

    session_list = list(sessions)
    total_sessions = len(session_list)

    if midterm_routine:
        midterm_sessions = [
            session for session in session_list
            if session.date <= midterm_routine.exam_date
        ]
    else:
        midpoint = total_sessions // 2
        midterm_sessions = session_list[:midpoint]

    if final_routine:
        final_sessions = [
            session for session in session_list
            if session.date <= final_routine.exam_date
        ]
    else:
        final_sessions = session_list

    student_rows = []

    for reg in registrations:
        student = reg.student

        present_count = 0
        mid_present_count = 0
        final_present_count = 0

        session_statuses = []

        for session in session_list:
            is_present = attendance_lookup.get((student.id, session.id), False)

            if is_present:
                present_count += 1

            if session in midterm_sessions and is_present:
                mid_present_count += 1

            if session in final_sessions and is_present:
                final_present_count += 1

            session_statuses.append({
                'session': session,
                'is_present': is_present,
            })

        if total_sessions > 0:
            overall_percentage = round((present_count / total_sessions) * 100, 2)
        else:
            overall_percentage = 0

        if len(midterm_sessions) > 0:
            midterm_percentage = round((mid_present_count / len(midterm_sessions)) * 100, 2)
        else:
            midterm_percentage = 0

        if len(final_sessions) > 0:
            final_percentage = round((final_present_count / len(final_sessions)) * 100, 2)
        else:
            final_percentage = 0

        student_rows.append({
            'student': student,
            'session_statuses': session_statuses,
            'present_count': present_count,
            'absent_count': total_sessions - present_count,
            'midterm_percentage': midterm_percentage,
            'final_percentage': final_percentage,
            'overall_percentage': overall_percentage,
        })

    context = {
        'course_offering': course_offering,
        'registrations': registrations,
        'sessions': session_list,
        'student_rows': student_rows,
        'total_sessions': total_sessions,
        'midterm_routine': midterm_routine,
        'final_routine': final_routine,
    }

    return render(request, 'dashboard/take_attendance.html', context)
@login_required
def delete_attendance_session(request, session_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    session = get_object_or_404(
        AttendanceSession.objects.select_related('course_offering'),
        id=session_id,
        course_offering__faculty=request.user
    )

    offering_id = session.course_offering.id

    if request.method == 'POST':
        session.delete()
        messages.success(request, "Attendance session deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('faculty_course_students', offering_id=offering_id)


@login_required
def enter_marks(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering.objects.select_related(
            'course',
            'batch',
            'semester'
        ),
        id=offering_id,
        faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user'
    ).order_by(
        'student__student_id'
    )

    published_result_exists = ResultPublication.objects.filter(
        course_offering=course_offering,
        is_published=True
    ).exists()

    if request.method == 'POST':
        if published_result_exists:
            messages.error(
                request,
                (
                    'Marks for this course cannot be edited directly because '
                    'a result has already been published. Use the result '
                    'correction workflow instead.'
                )
            )

            return redirect(
                'enter_marks',
                offering_id=course_offering.id
            )

        for reg in registrations:
            student = reg.student

            try:
                class_test = Decimal(
                    request.POST.get(
                        f'class_test_{student.id}'
                    ) or '0'
                )

                assignment = Decimal(
                    request.POST.get(
                        f'assignment_{student.id}'
                    ) or '0'
                )

                attendance = Decimal(
                    request.POST.get(
                        f'attendance_{student.id}'
                    ) or '0'
                )

                midterm = Decimal(
                    request.POST.get(
                        f'midterm_{student.id}'
                    ) or '0'
                )

                final = Decimal(
                    request.POST.get(
                        f'final_{student.id}'
                    ) or '0'
                )

            except Exception:
                messages.error(
                    request,
                    (
                        f'Invalid mark value found for student '
                        f'{student.student_id}.'
                    )
                )

                return redirect(
                    'enter_marks',
                    offering_id=course_offering.id
                )

            mark, created = Mark.objects.get_or_create(
                student=student,
                course_offering=course_offering
            )

            mark.class_test = class_test
            mark.assignment = assignment
            mark.attendance = attendance
            mark.midterm = midterm
            mark.final = final

            if created or not mark.submitted_by:
                mark.submitted_by = request.user
                mark.submitted_at = timezone.now()

            mark.last_updated_by = request.user
            mark.last_updated_at = timezone.now()
            mark.is_submitted = True

            mark.save()

        messages.success(
            request,
            'Marks submitted successfully.'
        )

        return redirect(
            'faculty_course_students',
            offering_id=course_offering.id
        )

    existing_marks = Mark.objects.filter(
        course_offering=course_offering
    ).select_related(
        'student',
        'student__user'
    )

    marks_dict = {
        mark.student.id: mark
        for mark in existing_marks
    }

    student_rows = []

    for reg in registrations:
        mark = marks_dict.get(
            reg.student.id
        )

        active_correction_exists = False

        if mark:
            active_correction_exists = (
                ResultCorrectionRequest.objects.filter(
                    mark=mark,
                    status__in=[
                        'pending',
                        'faculty_submitted',
                        'exam_verified',
                    ]
                ).exists()
            )

        student_rows.append({
            'student': reg.student,
            'mark': mark,
            'active_correction_exists': active_correction_exists,
        })

    context = {
        'course_offering': course_offering,
        'student_rows': student_rows,
        'published_result_exists': published_result_exists,
    }

    return render(
        request,
        'dashboard/enter_marks.html',
        context
    )

@login_required
def course_materials(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering,
        id=offering_id,
        faculty=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')

        if title and file:
            CourseMaterial.objects.create(
                course_offering=course_offering,
                title=title,
                file=file
            )
            messages.success(request, "Course material uploaded successfully.")
        else:
            messages.error(request, "Please enter title and choose a file.")

        return redirect('course_materials', offering_id=course_offering.id)

    materials = CourseMaterial.objects.filter(
        course_offering=course_offering
    ).order_by('-uploaded_at')

    context = {
        'course_offering': course_offering,
        'materials': materials,
    }

    return render(request, 'dashboard/course_materials.html', context)


@login_required
def delete_course_material(request, material_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    material = get_object_or_404(
        CourseMaterial.objects.select_related('course_offering'),
        id=material_id,
        course_offering__faculty=request.user
    )

    offering_id = material.course_offering.id

    if request.method == 'POST':
        material.delete()
        messages.success(request, "Course material deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('course_materials', offering_id=offering_id)


@login_required
def faculty_assignments(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering,
        id=offering_id,
        faculty=request.user
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_assignment':
            title = request.POST.get('title')
            description = request.POST.get('description')
            deadline = request.POST.get('deadline')
            total_marks = Decimal(request.POST.get('total_marks') or '10')
            attachment = request.FILES.get('attachment')
            is_published = True if request.POST.get('is_published') else False

            if title and deadline:
                Assignment.objects.create(
                    course_offering=course_offering,
                    title=title,
                    description=description,
                    deadline=deadline,
                    total_marks=total_marks,
                    attachment=attachment,
                    is_published=is_published,
                    accepting_submissions=True
                )
                messages.success(request, "Assignment created successfully.")
            else:
                messages.error(request, "Please enter assignment title and deadline.")

        elif action == 'publish':
            assignment_id = request.POST.get('assignment_id')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment:
                assignment.is_published = True
                assignment.save()
                messages.success(request, "Assignment published successfully.")

        elif action == 'unpublish':
            assignment_id = request.POST.get('assignment_id')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment:
                assignment.is_published = False
                assignment.save()
                messages.warning(request, "Assignment unpublished successfully.")

        elif action == 'pause_submission':
            assignment_id = request.POST.get('assignment_id')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment:
                assignment.accepting_submissions = False
                assignment.save()
                messages.warning(request, "Assignment submission paused.")

        elif action == 'resume_submission':
            assignment_id = request.POST.get('assignment_id')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment:
                assignment.accepting_submissions = True
                assignment.save()
                messages.success(request, "Assignment submission resumed.")

        elif action == 'extend_deadline':
            assignment_id = request.POST.get('assignment_id')
            new_deadline = request.POST.get('new_deadline')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment and new_deadline:
                assignment.deadline = new_deadline
                assignment.accepting_submissions = True
                assignment.save()
                messages.success(request, "Assignment deadline extended successfully.")
            else:
                messages.error(request, "Please select a new deadline.")

        elif action == 'delete_assignment':
            assignment_id = request.POST.get('assignment_id')

            assignment = Assignment.objects.filter(
                id=assignment_id,
                course_offering=course_offering
            ).first()

            if assignment:
                assignment.delete()
                messages.success(request, "Assignment deleted successfully.")

        return redirect('faculty_assignments', offering_id=course_offering.id)

    assignments = Assignment.objects.filter(
        course_offering=course_offering
    ).order_by('-created_at')

    total_students = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).count()

    assignment_rows = []
    now = timezone.now()

    for assignment in assignments:
        submitted_count = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).count()

        not_submitted_count = total_students - submitted_count

        is_deadline_over = assignment.deadline < now

        submission_open = (
            assignment.is_published and
            assignment.accepting_submissions and
            not is_deadline_over
        )

        assignment_rows.append({
            'assignment': assignment,
            'submitted_count': submitted_count,
            'not_submitted_count': not_submitted_count,
            'is_deadline_over': is_deadline_over,
            'submission_open': submission_open,
        })

    context = {
        'course_offering': course_offering,
        'assignment_rows': assignment_rows,
        'now': now,
    }

    return render(request, 'dashboard/faculty_assignments.html', context)


@login_required
def edit_assignment(request, assignment_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester'
        ),
        id=assignment_id,
        course_offering__faculty=request.user
    )

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        total_marks = Decimal(request.POST.get('total_marks') or '10')
        attachment = request.FILES.get('attachment')

        assignment.title = title
        assignment.description = description
        assignment.total_marks = total_marks

        if deadline:
            assignment.deadline = deadline

        if attachment:
            assignment.attachment = attachment

        assignment.is_published = True if request.POST.get('is_published') else False
        assignment.accepting_submissions = True if request.POST.get('accepting_submissions') else False

        assignment.save()

        messages.success(request, "Assignment updated successfully.")
        return redirect('faculty_assignments', offering_id=assignment.course_offering.id)

    context = {
        'assignment': assignment,
    }

    return render(request, 'dashboard/edit_assignment.html', context)


@login_required
def faculty_assignment_submissions(request, assignment_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester'
        ),
        id=assignment_id,
        course_offering__faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=assignment.course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_marks':
            for reg in registrations:
                student = reg.student
                submission = AssignmentSubmission.objects.filter(
                    assignment=assignment,
                    student=student
                ).first()

                if submission:
                    obtained_marks = request.POST.get(f'obtained_marks_{submission.id}')
                    feedback = request.POST.get(f'feedback_{submission.id}')

                    if obtained_marks != '':
                        submission.obtained_marks = Decimal(obtained_marks or '0')

                    submission.feedback = feedback
                    submission.status = 'checked'
                    submission.save()

            messages.success(request, "Assignment marks and feedback saved successfully.")

        elif action == 'pause_submission':
            assignment.accepting_submissions = False
            assignment.save()
            messages.warning(request, "Assignment submission paused.")

        elif action == 'resume_submission':
            assignment.accepting_submissions = True
            assignment.save()
            messages.success(request, "Assignment submission resumed.")

        elif action == 'extend_deadline':
            new_deadline = request.POST.get('new_deadline')

            if new_deadline:
                assignment.deadline = new_deadline
                assignment.accepting_submissions = True
                assignment.save()
                messages.success(request, "Assignment deadline extended successfully.")
            else:
                messages.error(request, "Please select a new deadline.")

        return redirect('faculty_assignment_submissions', assignment_id=assignment.id)

    submission_dict = {
        submission.student_id: submission
        for submission in AssignmentSubmission.objects.filter(
            assignment=assignment
        ).select_related('student', 'student__user')
    }

    student_rows = []

    for reg in registrations:
        submission = submission_dict.get(reg.student.id)

        student_rows.append({
            'student': reg.student,
            'submission': submission,
            'submitted': True if submission else False,
        })

    submitted_count = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).count()

    total_students = registrations.count()
    not_submitted_count = total_students - submitted_count

    now = timezone.now()
    is_deadline_over = assignment.deadline < now

    submission_open = (
        assignment.is_published and
        assignment.accepting_submissions and
        not is_deadline_over
    )

    context = {
        'assignment': assignment,
        'student_rows': student_rows,
        'total_students': total_students,
        'submitted_count': submitted_count,
        'not_submitted_count': not_submitted_count,
        'is_deadline_over': is_deadline_over,
        'submission_open': submission_open,
    }

    return render(request, 'dashboard/faculty_assignment_submissions.html', context)


@login_required
def faculty_reports(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    assigned_courses = CourseOffering.objects.filter(
        faculty=request.user,
        is_active=True
    ).select_related(
        'course',
        'batch',
        'semester'
    )

    report_rows = []

    for course_offering in assigned_courses:
        registrations = CourseRegistration.objects.filter(
            course_offering=course_offering,
            status='approved'
        )

        total_students = registrations.count()

        total_classes = AttendanceSession.objects.filter(
            course_offering=course_offering
        ).count()

        total_present_records = AttendanceRecord.objects.filter(
            session__course_offering=course_offering,
            is_present=True
        ).count()

        if total_students > 0 and total_classes > 0:
            average_attendance = round(
                (total_present_records / (total_students * total_classes)) * 100,
                2
            )
        else:
            average_attendance = 0

        total_assignments = Assignment.objects.filter(
            course_offering=course_offering
        ).count()

        published_assignments = Assignment.objects.filter(
            course_offering=course_offering,
            is_published=True
        ).count()

        total_assignment_submissions = AssignmentSubmission.objects.filter(
            assignment__course_offering=course_offering
        ).count()

        checked_submissions = AssignmentSubmission.objects.filter(
            assignment__course_offering=course_offering,
            status='checked'
        ).count()

        marks_submitted = Mark.objects.filter(
            course_offering=course_offering,
            is_submitted=True
        ).count()

        report_rows.append({
            'course_offering': course_offering,
            'total_students': total_students,
            'total_classes': total_classes,
            'average_attendance': average_attendance,
            'total_assignments': total_assignments,
            'published_assignments': published_assignments,
            'total_assignment_submissions': total_assignment_submissions,
            'checked_submissions': checked_submissions,
            'marks_submitted': marks_submitted,
        })

    context = {
        'report_rows': report_rows,
    }

    return render(request, 'dashboard/faculty_reports.html', context)


@login_required
def faculty_course_report(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering.objects.select_related(
            'course',
            'batch',
            'semester'
        ),
        id=offering_id,
        faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    )

    total_students = registrations.count()

    total_classes = AttendanceSession.objects.filter(
        course_offering=course_offering
    ).count()

    assignments = Assignment.objects.filter(
        course_offering=course_offering
    ).order_by('-created_at')

    total_assignments = assignments.count()

    total_submissions = AssignmentSubmission.objects.filter(
        assignment__course_offering=course_offering
    ).count()

    checked_submissions = AssignmentSubmission.objects.filter(
        assignment__course_offering=course_offering,
        status='checked'
    ).count()

    marks_submitted_count = Mark.objects.filter(
        course_offering=course_offering,
        is_submitted=True
    ).count()

    student_rows = []

    total_attendance_percent_sum = 0
    attendance_count = 0

    for reg in registrations:
        student = reg.student

        present_classes = AttendanceRecord.objects.filter(
            student=student,
            session__course_offering=course_offering,
            is_present=True
        ).count()

        absent_classes = total_classes - present_classes

        if total_classes > 0:
            attendance_percent = round(
                (present_classes / total_classes) * 100,
                2
            )
            total_attendance_percent_sum += attendance_percent
            attendance_count += 1
        else:
            attendance_percent = 0

        mark = Mark.objects.filter(
            student=student,
            course_offering=course_offering
        ).first()

        submitted_assignments = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course_offering=course_offering
        ).count()

        checked_assignments = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course_offering=course_offering,
            status='checked'
        ).count()

        assignment_marks_total = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course_offering=course_offering,
            status='checked'
        ).aggregate(total=Sum('obtained_marks'))['total'] or 0

        student_rows.append({
            'student': student,
            'present_classes': present_classes,
            'absent_classes': absent_classes,
            'attendance_percent': attendance_percent,
            'mark': mark,
            'submitted_assignments': submitted_assignments,
            'checked_assignments': checked_assignments,
            'assignment_marks_total': assignment_marks_total,
        })

    if attendance_count > 0:
        course_average_attendance = round(
            total_attendance_percent_sum / attendance_count,
            2
        )
    else:
        course_average_attendance = 0

    context = {
        'course_offering': course_offering,

        'total_students': total_students,
        'total_classes': total_classes,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'checked_submissions': checked_submissions,
        'marks_submitted_count': marks_submitted_count,
        'course_average_attendance': course_average_attendance,

        'student_rows': student_rows,
    }

    return render(request, 'dashboard/faculty_course_report.html', context)


@login_required
def download_faculty_course_report(request, offering_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    course_offering = get_object_or_404(
        CourseOffering.objects.select_related(
            'course',
            'batch',
            'semester'
        ),
        id=offering_id,
        faculty=request.user
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user'
    )

    total_students = registrations.count()

    total_classes = AttendanceSession.objects.filter(
        course_offering=course_offering
    ).count()

    total_assignments = Assignment.objects.filter(
        course_offering=course_offering
    ).count()

    total_submissions = AssignmentSubmission.objects.filter(
        assignment__course_offering=course_offering
    ).count()

    checked_submissions = AssignmentSubmission.objects.filter(
        assignment__course_offering=course_offering,
        status='checked'
    ).count()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="Course_Report_{course_offering.course.code}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 50

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, "University of Global Village (UGV)")

    y -= 28
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Course Performance Report")

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Course: {course_offering.course.code} - {course_offering.course.title}")

    y -= 18
    p.drawString(50, y, f"Batch: {course_offering.batch}")

    y -= 18
    p.drawString(50, y, f"Semester: {course_offering.semester}")

    y -= 18
    p.drawString(50, y, f"Section: {course_offering.section}")

    y -= 18
    p.drawString(50, y, f"Faculty: {request.user.username}")

    y -= 30
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Course Summary")

    y -= 20
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Total Students: {total_students}")
    p.drawString(220, y, f"Total Classes: {total_classes}")

    y -= 18
    p.drawString(50, y, f"Assignments: {total_assignments}")
    p.drawString(220, y, f"Submissions: {total_submissions}")
    p.drawString(390, y, f"Checked: {checked_submissions}")

    y -= 35
    p.setFont("Helvetica-Bold", 8)
    p.drawString(35, y, "Student ID")
    p.drawString(115, y, "Name")
    p.drawString(225, y, "Att%")
    p.drawString(265, y, "Quiz/CT")
    p.drawString(300, y, "Assign")
    p.drawString(350, y, "Att Mark")
    p.drawString(405, y, "Mid")
    p.drawString(445, y, "Final")
    p.drawString(490, y, "Total")
    p.drawString(535, y, "Grade")

    y -= 8
    p.line(35, y, 560, y)

    y -= 18
    p.setFont("Helvetica", 8)

    for reg in registrations:
        student = reg.student

        present_classes = AttendanceRecord.objects.filter(
            student=student,
            session__course_offering=course_offering,
            is_present=True
        ).count()

        if total_classes > 0:
            attendance_percent = round((present_classes / total_classes) * 100, 2)
        else:
            attendance_percent = 0

        mark = Mark.objects.filter(
            student=student,
            course_offering=course_offering
        ).first()

        if y < 60:
            p.showPage()
            y = height - 50

            p.setFont("Helvetica-Bold", 8)
            p.drawString(35, y, "Student ID")
            p.drawString(115, y, "Name")
            p.drawString(225, y, "Att%")
            p.drawString(265, y, "Quiz/CT")
            p.drawString(300, y, "Assign")
            p.drawString(350, y, "Att Mark")
            p.drawString(405, y, "Mid")
            p.drawString(445, y, "Final")
            p.drawString(490, y, "Total")
            p.drawString(535, y, "Grade")

            y -= 18
            p.setFont("Helvetica", 8)

        name = student.user.get_full_name() or student.user.username

        p.drawString(35, y, student.student_id)
        p.drawString(115, y, name[:17])
        p.drawString(225, y, str(attendance_percent))

        if mark and mark.is_submitted:
            p.drawString(265, y, str(mark.class_test))
            p.drawString(300, y, str(mark.assignment))
            p.drawString(350, y, str(mark.attendance))
            p.drawString(405, y, str(mark.midterm))
            p.drawString(445, y, str(mark.final))
            p.drawString(490, y, str(mark.total))
            p.drawString(535, y, str(mark.grade))
        else:
            p.drawString(265, y, "-")
            p.drawString(300, y, "-")
            p.drawString(350, y, "-")
            p.drawString(405, y, "-")
            p.drawString(445, y, "-")
            p.drawString(490, y, "-")
            p.drawString(535, y, "-")

        y -= 18

    p.showPage()
    p.save()

    return response


@login_required
def faculty_applications(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    applications = StudentApplication.objects.filter(
        to_user=request.user
    ).select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch'
    ).order_by('-submitted_at')

    context = {
        'applications': applications,
    }

    return render(request, 'dashboard/faculty_applications.html', context)


@login_required
def faculty_application_detail(request, application_id):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    application = get_object_or_404(
        StudentApplication,
        id=application_id,
        to_user=request.user
    )

    if request.method == 'POST':
        status = request.POST.get('status')
        reply = request.POST.get('reply')

        if status:
            application.status = status

        application.reply = reply
        application.save()

        messages.success(request, "Application reply updated successfully.")
        return redirect('faculty_applications')

    context = {
        'application': application,
    }

    return render(request, 'dashboard/faculty_application_detail.html', context)


@login_required
def faculty_hall_duties(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    hall_duties = HallDuty.objects.filter(
        faculty=request.user
    ).select_related(
        'exam_routine',
        'exam_routine__course_offering',
        'exam_routine__course_offering__course',
        'exam_routine__course_offering__batch',
        'exam_routine__course_offering__semester'
    ).order_by(
        'exam_routine__exam_date',
        'exam_routine__start_time'
    )

    context = {
        'hall_duties': hall_duties,
    }

    return render(request, 'dashboard/faculty_hall_duties.html', context)

@login_required
def faculty_mark_review_requests(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    status_filter = request.GET.get('status', '').strip()

    review_requests = (
        StudentMarkReviewRequest.objects
        .select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'mark',
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester',
            'faculty_reviewed_by',
        )
        .filter(
            course_offering__faculty=request.user
        )
        .order_by('-created_at')
    )

    if status_filter:
        review_requests = review_requests.filter(
            status=status_filter
        )

    context = {
        'review_requests': review_requests,
        'status_filter': status_filter,
        'pending_count': StudentMarkReviewRequest.objects.filter(
            course_offering__faculty=request.user,
            status='pending_faculty'
        ).count(),
        'confirmed_count': StudentMarkReviewRequest.objects.filter(
            course_offering__faculty=request.user,
            status='faculty_confirmed'
        ).count(),
        'rejected_count': StudentMarkReviewRequest.objects.filter(
            course_offering__faculty=request.user,
            status='faculty_rejected'
        ).count(),
    }

    return render(
        request,
        'dashboard/faculty_mark_review_requests.html',
        context
    )


@login_required
def faculty_mark_review_request_detail(
    request,
    review_request_id
):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    review_request = get_object_or_404(
        StudentMarkReviewRequest.objects.select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester',
            'mark',
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester',
            'faculty_reviewed_by',
        ),
        id=review_request_id,
        course_offering__faculty=request.user
    )

    existing_correction = (
        ResultCorrectionRequest.objects
        .filter(
            student_review_request=review_request
        )
        .select_related(
            'requested_by',
            'exam_reviewed_by',
            'reviewed_by',
        )
        .first()
    )

    if request.method == 'POST':
        if review_request.status != 'pending_faculty':
            messages.warning(
                request,
                'This student review request has already been reviewed.'
            )

            return redirect(
                'faculty_mark_review_request_detail',
                review_request_id=review_request.id
            )

        action = request.POST.get('action')
        faculty_note = request.POST.get(
            'faculty_note',
            ''
        ).strip()

        if action == 'reject':
            review_request.reject_by_faculty(
                request.user,
                faculty_note
            )

            messages.warning(
                request,
                'Student mark review request rejected.'
            )

            return redirect(
                'faculty_mark_review_request_detail',
                review_request_id=review_request.id
            )

        if action == 'confirm_and_create_correction':
            try:
                new_class_test = Decimal(
                    request.POST.get('class_test') or '0'
                )
                new_assignment = Decimal(
                    request.POST.get('assignment') or '0'
                )
                new_attendance = Decimal(
                    request.POST.get('attendance') or '0'
                )
                new_midterm = Decimal(
                    request.POST.get('midterm') or '0'
                )
                new_final = Decimal(
                    request.POST.get('final') or '0'
                )
            except Exception:
                messages.error(
                    request,
                    'One or more corrected mark values are invalid.'
                )

                return redirect(
                    'faculty_mark_review_request_detail',
                    review_request_id=review_request.id
                )

            correction_reason = request.POST.get(
                'correction_reason',
                ''
            ).strip()

            faculty_attachment = request.FILES.get(
                'faculty_attachment'
            )

            if not correction_reason:
                messages.error(
                    request,
                    'Please provide the official correction reason.'
                )

                return redirect(
                    'faculty_mark_review_request_detail',
                    review_request_id=review_request.id
                )

            active_request_exists = (
                ResultCorrectionRequest.objects
                .filter(
                    mark=review_request.mark,
                    status__in=[
                        'pending',
                        'faculty_submitted',
                        'exam_verified',
                    ]
                )
                .exists()
            )

            if active_request_exists:
                messages.warning(
                    request,
                    (
                        'An active correction request already exists '
                        'for this result.'
                    )
                )

                return redirect(
                    'faculty_mark_review_request_detail',
                    review_request_id=review_request.id
                )

            correction_request = (
                ResultCorrectionRequest.objects.create(
                    mark=review_request.mark,
                    student=review_request.student,
                    course_offering=review_request.course_offering,
                    student_review_request=review_request,
                    requested_by=request.user,
                    reason=correction_reason,
                    faculty_attachment=faculty_attachment,

                    old_class_test=review_request.mark.class_test,
                    old_assignment=review_request.mark.assignment,
                    old_attendance=review_request.mark.attendance,
                    old_midterm=review_request.mark.midterm,
                    old_final=review_request.mark.final,

                    new_class_test=new_class_test,
                    new_assignment=new_assignment,
                    new_attendance=new_attendance,
                    new_midterm=new_midterm,
                    new_final=new_final,

                    status='faculty_submitted',
                )
            )

            review_request.confirm_by_faculty(
                request.user,
                faculty_note
            )

            messages.success(
                request,
                (
                    'Student request confirmed and official correction '
                    'request sent to the Exam Controller.'
                )
            )

            return redirect(
                'faculty_correction_request_detail',
                correction_request_id=correction_request.id
            )

        messages.error(
            request,
            'Invalid review action.'
        )

    context = {
        'review_request': review_request,
        'existing_correction': existing_correction,
    }

    return render(
        request,
        'dashboard/faculty_mark_review_request_detail.html',
        context
    )


@login_required
def faculty_correction_requests(request):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    correction_requests = (
        ResultCorrectionRequest.objects
        .select_related(
            'student',
            'student__user',
            'student__department',
            'mark',
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester',
            'student_review_request',
            'exam_reviewed_by',
            'reviewed_by',
        )
        .filter(
            requested_by=request.user
        )
        .order_by('-created_at')
    )

    context = {
        'correction_requests': correction_requests,
    }

    return render(
        request,
        'dashboard/faculty_correction_requests.html',
        context
    )


@login_required
def faculty_create_correction_request(
    request,
    mark_id
):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    mark = get_object_or_404(
        Mark.objects.select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester',
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester',
        ),
        id=mark_id,
        is_submitted=True,
        course_offering__faculty=request.user
    )

    active_request = (
        ResultCorrectionRequest.objects
        .filter(
            mark=mark,
            status__in=[
                'pending',
                'faculty_submitted',
                'exam_verified',
            ]
        )
        .first()
    )

    if request.method == 'POST':
        if active_request:
            messages.warning(
                request,
                'An active correction request already exists for this result.'
            )

            return redirect(
                'faculty_create_correction_request',
                mark_id=mark.id
            )

        try:
            new_class_test = Decimal(
                request.POST.get('class_test') or '0'
            )
            new_assignment = Decimal(
                request.POST.get('assignment') or '0'
            )
            new_attendance = Decimal(
                request.POST.get('attendance') or '0'
            )
            new_midterm = Decimal(
                request.POST.get('midterm') or '0'
            )
            new_final = Decimal(
                request.POST.get('final') or '0'
            )
        except Exception:
            messages.error(
                request,
                'One or more corrected mark values are invalid.'
            )

            return redirect(
                'faculty_create_correction_request',
                mark_id=mark.id
            )

        reason = request.POST.get(
            'reason',
            ''
        ).strip()

        faculty_attachment = request.FILES.get(
            'faculty_attachment'
        )

        if not reason:
            messages.error(
                request,
                'Please provide the reason for the correction.'
            )

            return redirect(
                'faculty_create_correction_request',
                mark_id=mark.id
            )

        correction_request = (
            ResultCorrectionRequest.objects.create(
                mark=mark,
                student=mark.student,
                course_offering=mark.course_offering,
                requested_by=request.user,
                reason=reason,
                faculty_attachment=faculty_attachment,

                old_class_test=mark.class_test,
                old_assignment=mark.assignment,
                old_attendance=mark.attendance,
                old_midterm=mark.midterm,
                old_final=mark.final,

                new_class_test=new_class_test,
                new_assignment=new_assignment,
                new_attendance=new_attendance,
                new_midterm=new_midterm,
                new_final=new_final,

                status='faculty_submitted',
            )
        )

        messages.success(
            request,
            (
                'Official correction request submitted '
                'to the Exam Controller.'
            )
        )

        return redirect(
            'faculty_correction_request_detail',
            correction_request_id=correction_request.id
        )

    context = {
        'mark': mark,
        'active_request': active_request,
    }

    return render(
        request,
        'dashboard/faculty_create_correction_request.html',
        context
    )


@login_required
def faculty_correction_request_detail(
    request,
    correction_request_id
):
    if request.user.role != 'faculty':
        return redirect('dashboard')

    correction_request = get_object_or_404(
        ResultCorrectionRequest.objects.select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester',
            'mark',
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester',
            'student_review_request',
            'exam_reviewed_by',
            'reviewed_by',
        ),
        id=correction_request_id,
        requested_by=request.user
    )

    mark_changes = [
        {
            'label': 'Class Test',
            'old': correction_request.old_class_test,
            'new': correction_request.new_class_test,
        },
        {
            'label': 'Assignment',
            'old': correction_request.old_assignment,
            'new': correction_request.new_assignment,
        },
        {
            'label': 'Attendance',
            'old': correction_request.old_attendance,
            'new': correction_request.new_attendance,
        },
        {
            'label': 'Midterm',
            'old': correction_request.old_midterm,
            'new': correction_request.new_midterm,
        },
        {
            'label': 'Final',
            'old': correction_request.old_final,
            'new': correction_request.new_final,
        },
    ]

    for item in mark_changes:
        item['changed'] = (
            item['old'] != item['new']
        )
        item['difference'] = (
            item['new'] - item['old']
        )

    context = {
        'correction_request': correction_request,
        'mark_changes': mark_changes,
    }

    return render(
        request,
        'dashboard/faculty_correction_request_detail.html',
        context
    )
