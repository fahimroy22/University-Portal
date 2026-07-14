from decimal import Decimal
from django.contrib.auth import logout

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from accounts.models import User
from academics.models import Department, CourseOffering, CourseMaterial
from students.models import StudentProfile, CourseRegistration
from finance.models import FeeType, StudentFee, Payment, Waiver
from faculty.models import AttendanceSession, AttendanceRecord, Mark, Assignment, AssignmentSubmission
from applications.models import StudentApplication
from exams.models import ExamRoutine, SeatPlan, HallDuty, ResultPublication



@login_required
def dashboard_redirect(request):
    user = request.user

    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'faculty':
        return redirect('faculty_dashboard')
    elif user.role == 'dept_head':
        return redirect('dept_head_dashboard')
    elif user.role == 'exam_controller':
        return redirect('exam_controller_dashboard')
    elif user.role == 'accounts':
        return redirect('accounts_dashboard')
    elif user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'super_admin':
        return redirect('super_admin_dashboard')

    return redirect('login')


def calculate_student_dashboard_data(user):
    profile = None
    current_courses = []
    attendance_summary = []
    result_summary = []
    midterm_results = []
    final_results = []
    semester_results = []
    course_materials = []
    recent_applications = []
    exam_routines = []
    seat_plans = []

    total_payable = 0
    total_paid = 0
    total_waiver = 0
    current_due = 0
    credit_balance = 0

    admit_payment_ok = False
    admit_attendance_ok = False
    admit_final_eligible = False
    average_attendance = 0

    overall_cgpa = 0
    total_result_credits = Decimal('0')
    total_weighted_points = Decimal('0')

    if user.role == 'student':
        profile = StudentProfile.objects.filter(user=user).first()

        if profile:
            current_courses = CourseRegistration.objects.filter(
                student=profile,
                status='approved'
            ).select_related(
                'course_offering',
                'course_offering__course',
                'course_offering__faculty'
            )

            course_offering_ids = current_courses.values_list(
                'course_offering_id',
                flat=True
            )

            course_materials = CourseMaterial.objects.filter(
                course_offering_id__in=course_offering_ids
            ).select_related(
                'course_offering',
                'course_offering__course'
            ).order_by('-uploaded_at')

            recent_applications = StudentApplication.objects.filter(
                student=profile
            ).select_related(
                'to_user'
            ).order_by('-submitted_at')[:5]

            exam_routines = ExamRoutine.objects.filter(
                course_offering_id__in=course_offering_ids,
                is_published=True
            ).select_related(
                'course_offering',
                'course_offering__course'
            ).order_by('exam_date', 'start_time')

            seat_plans = SeatPlan.objects.filter(
                student=profile,
                course_offering_id__in=course_offering_ids,
                is_published=True
            ).select_related(
                'course_offering',
                'course_offering__course'
            ).order_by('course_offering__course__code')

            total_payable = StudentFee.objects.filter(
                student=profile
            ).aggregate(total=Sum('amount'))['total'] or 0

            total_paid = Payment.objects.filter(
                student=profile
            ).aggregate(total=Sum('amount'))['total'] or 0

            total_waiver = Waiver.objects.filter(
                student=profile
            ).aggregate(total=Sum('amount'))['total'] or 0

            balance = total_payable - total_paid - total_waiver

            if balance > 0:
                current_due = balance
                credit_balance = 0
            else:
                current_due = 0
                credit_balance = abs(balance)

            for reg in current_courses:
                course_offering = reg.course_offering

                total_classes = AttendanceSession.objects.filter(
                    course_offering=course_offering
                ).count()

                present_classes = AttendanceRecord.objects.filter(
                    student=profile,
                    session__course_offering=course_offering,
                    is_present=True
                ).count()

                absent_classes = total_classes - present_classes

                if total_classes > 0:
                    attendance_percent = round(
                        (present_classes / total_classes) * 100,
                        2
                    )
                else:
                    attendance_percent = 0

                attendance_summary.append({
                    'course_code': course_offering.course.code,
                    'course_title': course_offering.course.title,
                    'total_classes': total_classes,
                    'present_classes': present_classes,
                    'absent_classes': absent_classes,
                    'attendance_percent': attendance_percent,
                })

            midterm_published_offering_ids = ResultPublication.objects.filter(
                course_offering_id__in=course_offering_ids,
                exam_type='midterm',
                is_published=True
            ).values_list('course_offering_id', flat=True)

            final_published_offering_ids = ResultPublication.objects.filter(
                course_offering_id__in=course_offering_ids,
                exam_type='final',
                is_published=True
            ).values_list('course_offering_id', flat=True)

            midterm_results = Mark.objects.filter(
                student=profile,
                is_submitted=True,
                course_offering_id__in=midterm_published_offering_ids
            ).select_related(
                'course_offering',
                'course_offering__course',
                'course_offering__semester'
            ).order_by(
                'course_offering__semester__id',
                'course_offering__course__code'
            )

            final_results = Mark.objects.filter(
                student=profile,
                is_submitted=True,
                course_offering_id__in=final_published_offering_ids
            ).select_related(
                'course_offering',
                'course_offering__course',
                'course_offering__semester'
            ).order_by(
                'course_offering__semester__id',
                'course_offering__course__code'
            )

            result_summary = final_results

            semester_dict = {}

            for mark in final_results:
                semester = mark.course_offering.semester
                semester_key = semester.id

                credit = mark.course_offering.course.credit or 0
                grade_point = mark.grade_point or 0

                credit_decimal = Decimal(str(credit))
                grade_point_decimal = Decimal(str(grade_point))
                weighted_point = credit_decimal * grade_point_decimal

                total_result_credits += credit_decimal
                total_weighted_points += weighted_point

                if semester_key not in semester_dict:
                    semester_dict[semester_key] = {
                        'semester': semester,
                        'courses': [],
                        'total_credits': Decimal('0'),
                        'total_weighted_points': Decimal('0'),
                        'semester_cgpa': 0,
                    }

                semester_dict[semester_key]['courses'].append(mark)
                semester_dict[semester_key]['total_credits'] += credit_decimal
                semester_dict[semester_key]['total_weighted_points'] += weighted_point

            for item in semester_dict.values():
                if item['total_credits'] > 0:
                    item['semester_cgpa'] = round(
                        item['total_weighted_points'] / item['total_credits'],
                        2
                    )
                else:
                    item['semester_cgpa'] = 0

                semester_results.append(item)

            if total_result_credits > 0:
                overall_cgpa = round(
                    total_weighted_points / total_result_credits,
                    2
                )
            else:
                overall_cgpa = 0

            admit_payment_ok = current_due <= 0

            attendance_percentages = [
                item['attendance_percent']
                for item in attendance_summary
                if item['total_classes'] > 0
            ]

            if attendance_percentages:
                average_attendance = round(
                    sum(attendance_percentages) / len(attendance_percentages),
                    2
                )
                admit_attendance_ok = average_attendance >= 60
            else:
                average_attendance = 0
                admit_attendance_ok = False

            admit_final_eligible = admit_payment_ok and admit_attendance_ok

    return {
        'profile': profile,
        'current_courses': current_courses,
        'course_materials': course_materials,
        'recent_applications': recent_applications,
        'exam_routines': exam_routines,
        'seat_plans': seat_plans,

        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_waiver': total_waiver,
        'current_due': current_due,
        'credit_balance': credit_balance,

        'attendance_summary': attendance_summary,
        'result_summary': result_summary,
        'midterm_results': midterm_results,
        'final_results': final_results,
        'semester_results': semester_results,
        'overall_cgpa': overall_cgpa,
        'total_result_credits': total_result_credits,

        'admit_payment_ok': admit_payment_ok,
        'admit_attendance_ok': admit_attendance_ok,
        'admit_final_eligible': admit_final_eligible,
        'average_attendance': average_attendance,
    }
@login_required
def student_dashboard(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
def submit_application(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.filter(user=request.user).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    recipients = User.objects.filter(
        role__in=[
            'faculty',
            'dept_head',
            'exam_controller',
            'accounts',
            'admin',
            'super_admin',
        ],
        is_active=True
    ).order_by('role', 'username')

    if request.method == 'POST':
        to_user_id = request.POST.get('to_user')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        to_user = User.objects.filter(id=to_user_id).first()

        if to_user and subject and message:
            StudentApplication.objects.create(
                student=profile,
                to_user=to_user,
                subject=subject,
                message=message
            )

            messages.success(request, "Application submitted successfully.")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Please fill all application fields.")

    context = {
        'profile': profile,
        'recipients': recipients,
    }

    return render(request, 'dashboard/submit_application.html', context)


@login_required
def download_admit_card(request):
    data = calculate_student_dashboard_data(request.user)

    profile = data['profile']
    current_courses = data['current_courses']
    current_due = data['current_due']
    credit_balance = data['credit_balance']
    average_attendance = data['average_attendance']
    admit_final_eligible = data['admit_final_eligible']

    if not profile:
        return HttpResponse("Student profile not found.")

    if not admit_final_eligible:
        return HttpResponse(
            "You are not eligible to download the admit card. "
            "Please clear payment dues and meet attendance requirements."
        )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="UGV_Admit_Card.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 60

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, y, "University of Global Village (UGV)")

    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Admit Card")

    y -= 50
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Name: {profile.user.get_full_name() or profile.user.username}")

    y -= 22
    p.drawString(60, y, f"Student ID: {profile.student_id}")

    y -= 22
    p.drawString(60, y, f"Department: {profile.department}")

    y -= 22
    p.drawString(60, y, f"Batch: {profile.batch}")

    y -= 22
    p.drawString(60, y, f"Current Semester: {profile.current_semester}")

    y -= 22
    p.drawString(60, y, "Exam Type: Final Examination")

    y -= 22
    p.drawString(60, y, f"Payment Due: {current_due} BDT")

    y -= 22
    p.drawString(60, y, f"Credit Balance: {credit_balance} BDT")

    y -= 22
    p.drawString(60, y, f"Average Attendance: {average_attendance}%")

    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y, "Registered Courses:")

    y -= 25
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, y, "Course Code")
    p.drawString(180, y, "Course Title")
    p.drawString(430, y, "Credit")

    y -= 15
    p.line(60, y, 530, y)

    y -= 20
    p.setFont("Helvetica", 10)

    for reg in current_courses:
        if y < 100:
            p.showPage()
            y = height - 60

        course = reg.course_offering.course
        p.drawString(60, y, course.code)
        p.drawString(180, y, course.title[:35])
        p.drawString(430, y, str(course.credit))
        y -= 20

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(60, y, "Student Signature")
    p.drawString(380, y, "Exam Controller Signature")

    y -= 10
    p.line(60, y, 170, y)
    p.line(380, y, 530, y)

    p.showPage()
    p.save()

    return response


@login_required
def student_profile_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_profile.html', context)


@login_required
def student_courses_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_courses.html', context)


@login_required
def student_payments_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_payments.html', context)


@login_required
def student_attendance_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_attendance.html', context)


@login_required
def student_exam_routine_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_exam_routine.html', context)


@login_required
def student_seat_plan_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_seat_plan.html', context)


@login_required
def student_results_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_results.html', context)

@login_required
def download_student_result_pdf(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    data = calculate_student_dashboard_data(request.user)

    profile = data['profile']
    midterm_results = data['midterm_results']
    final_results = data['final_results']
    semester_results = data['semester_results']
    overall_cgpa = data['overall_cgpa']
    total_result_credits = data['total_result_credits']

    if not profile:
        return HttpResponse("Student profile not found.")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_Result_Copy_{profile.student_id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 60

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, y, "University of Global Village (UGV)")

    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Student Result Copy")

    y -= 45
    p.setFont("Helvetica", 10)
    p.drawString(60, y, f"Name: {profile.user.get_full_name() or profile.user.username}")

    y -= 20
    p.drawString(60, y, f"Student ID: {profile.student_id}")

    y -= 20
    p.drawString(60, y, f"Department: {profile.department}")

    y -= 20
    p.drawString(60, y, f"Batch: {profile.batch}")

    y -= 30

    if midterm_results:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Published Midterm Results")
        y -= 22

        p.setFont("Helvetica-Bold", 8)
        p.drawString(35, y, "Course")
        p.drawString(120, y, "Quiz/CT")
        p.drawString(180, y, "Assign")
        p.drawString(240, y, "Attend")
        p.drawString(300, y, "Midterm")
        p.drawString(370, y, "Mid Total /90")

        y -= 8
        p.line(35, y, 560, y)

        y -= 18
        p.setFont("Helvetica", 8)

        for mark in midterm_results:
            mid_total = mark.class_test + mark.assignment + mark.attendance + mark.midterm

            p.drawString(35, y, str(mark.course_offering.course.code))
            p.drawString(120, y, str(mark.class_test))
            p.drawString(180, y, str(mark.assignment))
            p.drawString(240, y, str(mark.attendance))
            p.drawString(300, y, str(mark.midterm))
            p.drawString(370, y, str(mid_total))

            y -= 18

    if final_results:
        y -= 25

        if y < 160:
            p.showPage()
            y = height - 60

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Published Final Results")
        y -= 22

        p.setFont("Helvetica-Bold", 8)
        p.drawString(35, y, "Course")
        p.drawString(95, y, "Credit")
        p.drawString(135, y, "Quiz/CT")
        p.drawString(185, y, "Assign")
        p.drawString(235, y, "Attend")
        p.drawString(285, y, "Mid")
        p.drawString(330, y, "Final")
        p.drawString(375, y, "Raw")
        p.drawString(420, y, "Total")
        p.drawString(465, y, "Grade")
        p.drawString(510, y, "GP")

        y -= 8
        p.line(35, y, 560, y)

        y -= 18
        p.setFont("Helvetica", 8)

        for mark in final_results:
            if y < 80:
                p.showPage()
                y = height - 60

            p.drawString(35, y, str(mark.course_offering.course.code)[:10])
            p.drawString(95, y, str(mark.course_offering.course.credit))
            p.drawString(135, y, str(mark.class_test))
            p.drawString(185, y, str(mark.assignment))
            p.drawString(235, y, str(mark.attendance))
            p.drawString(285, y, str(mark.midterm))
            p.drawString(330, y, str(mark.final))
            p.drawString(375, y, str(mark.raw_total))
            p.drawString(420, y, str(mark.total))
            p.drawString(465, y, str(mark.grade))
            p.drawString(510, y, str(mark.grade_point))

            y -= 18

        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, f"Total Completed Credits: {total_result_credits}")

        y -= 18
        p.drawString(60, y, f"Overall CGPA: {overall_cgpa}")

    if not midterm_results and not final_results:
        p.setFont("Helvetica", 10)
        p.drawString(60, y, "No published result found.")

    p.showPage()
    p.save()

    return response

@login_required
def student_materials_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_materials.html', context)


@login_required
def student_applications_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_applications.html', context)


@login_required
def student_admit_card_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_admit_card.html', context)


@login_required
def faculty_dashboard(request):
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

    hall_duties = HallDuty.objects.filter(
        faculty=request.user
    ).select_related(
        'exam_routine',
        'exam_routine__course_offering',
        'exam_routine__course_offering__course'
    ).order_by(
        'exam_routine__exam_date',
        'exam_routine__start_time'
    )

    context = {
        'assigned_courses': assigned_courses,
        'hall_duties': hall_duties,
        'total_courses': assigned_courses.count(),
        'total_hall_duties': hall_duties.count(),
    }

    return render(request, 'dashboard/faculty_dashboard.html', context)


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
        CourseOffering,
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

    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        topic = request.POST.get('topic')

        if attendance_date:
            session = AttendanceSession.objects.create(
                course_offering=course_offering,
                date=attendance_date,
                topic=topic
            )

            for reg in registrations:
                student = reg.student
                is_present = request.POST.get(f'present_{student.id}') == 'on'

                AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    is_present=is_present
                )

            messages.success(request, "Attendance submitted successfully.")
            return redirect('faculty_course_students', offering_id=course_offering.id)
        else:
            messages.error(request, "Please select an attendance date.")

    context = {
        'course_offering': course_offering,
        'registrations': registrations,
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
        CourseOffering,
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

    if request.method == 'POST':
        for reg in registrations:
            student = reg.student

            class_test = Decimal(request.POST.get(f'class_test_{student.id}') or '0')
            assignment = Decimal(request.POST.get(f'assignment_{student.id}') or '0')
            attendance = Decimal(request.POST.get(f'attendance_{student.id}') or '0')
            midterm = Decimal(request.POST.get(f'midterm_{student.id}') or '0')
            final = Decimal(request.POST.get(f'final_{student.id}') or '0')

            mark, created = Mark.objects.get_or_create(
                student=student,
                course_offering=course_offering
            )

            mark.class_test = class_test
            mark.assignment = assignment
            mark.attendance = attendance
            mark.midterm = midterm
            mark.final = final
            mark.is_submitted = True
            mark.save()

        messages.success(request, "Marks submitted successfully.")
        return redirect('faculty_course_students', offering_id=course_offering.id)

    existing_marks = Mark.objects.filter(
        course_offering=course_offering
    )

    marks_dict = {
        mark.student.id: mark
        for mark in existing_marks
    }

    student_rows = []

    for reg in registrations:
        student_rows.append({
            'student': reg.student,
            'mark': marks_dict.get(reg.student.id)
        })

    context = {
        'course_offering': course_offering,
        'student_rows': student_rows,
    }

    return render(request, 'dashboard/enter_marks.html', context)


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
def student_assignments_page(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.filter(user=request.user).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    current_courses = CourseRegistration.objects.filter(
        student=profile,
        status='approved'
    )

    course_offering_ids = current_courses.values_list(
        'course_offering_id',
        flat=True
    )

    assignments = Assignment.objects.filter(
        course_offering_id__in=course_offering_ids,
        is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course'
    ).order_by('-deadline')

    submission_dict = {
        submission.assignment_id: submission
        for submission in AssignmentSubmission.objects.filter(
            student=profile,
            assignment__in=assignments
        )
    }

    now = timezone.now()
    assignment_rows = []

    for assignment in assignments:
        submission = submission_dict.get(assignment.id)
        is_deadline_over = assignment.deadline < now

        submission_open = (
            assignment.accepting_submissions and
            not is_deadline_over
        )

        assignment_rows.append({
            'assignment': assignment,
            'submission': submission,
            'is_deadline_over': is_deadline_over,
            'submission_open': submission_open,
        })

    context = {
        'profile': profile,
        'assignment_rows': assignment_rows,
    }

    return render(request, 'dashboard/student_assignments.html', context)


@login_required
def submit_assignment(request, assignment_id):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.filter(user=request.user).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'course_offering',
            'course_offering__course'
        ),
        id=assignment_id,
        is_published=True
    )

    is_registered = CourseRegistration.objects.filter(
        student=profile,
        course_offering=assignment.course_offering,
        status='approved'
    ).exists()

    if not is_registered:
        return HttpResponse("You are not registered for this course.")

    submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=profile
    ).first()

    now = timezone.now()
    is_deadline_over = assignment.deadline < now

    submission_open = (
        assignment.accepting_submissions and
        not is_deadline_over
    )

    if request.method == 'POST':
        if not submission_open:
            messages.error(request, "Submission is currently closed for this assignment.")
            return redirect('student_assignments_page')

        answer_text = request.POST.get('answer_text')
        submitted_file = request.FILES.get('submitted_file')

        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=profile
        )

        submission.answer_text = answer_text

        if submitted_file:
            submission.submitted_file = submitted_file

        submission.status = 'submitted'
        submission.save()

        messages.success(request, "Assignment submitted successfully.")
        return redirect('student_assignments_page')

    context = {
        'assignment': assignment,
        'submission': submission,
        'is_deadline_over': is_deadline_over,
        'submission_open': submission_open,
    }

    return render(request, 'dashboard/submit_assignment.html', context)


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
def accounts_dashboard(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    query = request.GET.get('q', '')

    students = StudentProfile.objects.select_related(
        'user',
        'department',
        'batch',
        'current_semester'
    )

    if query:
        students = (
            students.filter(student_id__icontains=query)
            | StudentProfile.objects.filter(user__username__icontains=query)
            | StudentProfile.objects.filter(user__first_name__icontains=query)
            | StudentProfile.objects.filter(user__last_name__icontains=query)
        )

    students = students.distinct().order_by('student_id')

    context = {
        'students': students,
        'query': query,
    }

    return render(request, 'dashboard/accounts_dashboard.html', context)


@login_required
def accounts_student_detail(request, student_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'department',
            'batch',
            'current_semester'
        ),
        id=student_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_fee':
            fee_type_id = request.POST.get('fee_type')
            amount = Decimal(request.POST.get('amount') or '0')
            due_date = request.POST.get('due_date') or None

            fee_type = FeeType.objects.filter(id=fee_type_id).first()

            if fee_type and amount > 0:
                StudentFee.objects.create(
                    student=student,
                    fee_type=fee_type,
                    amount=amount,
                    due_date=due_date,
                    is_paid=False
                )
                messages.success(request, "Payable fee added successfully.")
            else:
                messages.error(request, "Please select fee type and enter valid amount.")

        elif action == 'add_payment':
            amount = Decimal(request.POST.get('amount') or '0')
            note = request.POST.get('note')

            if amount > 0:
                Payment.objects.create(
                    student=student,
                    amount=amount,
                    received_by=request.user.username,
                    note=note
                )
                messages.success(request, "Payment added successfully.")
            else:
                messages.error(request, "Please enter a valid payment amount.")

        elif action == 'add_waiver':
            amount = Decimal(request.POST.get('amount') or '0')
            reason = request.POST.get('reason')

            if amount > 0 and reason:
                Waiver.objects.create(
                    student=student,
                    amount=amount,
                    reason=reason,
                    approved_by=request.user.username
                )
                messages.success(request, "Waiver added successfully.")
            else:
                messages.error(request, "Please enter valid waiver amount and reason.")

        elif action == 'mark_fee_paid':
            fee_id = request.POST.get('fee_id')
            fee = StudentFee.objects.filter(id=fee_id, student=student).first()

            if fee:
                fee.is_paid = True
                fee.save()
                messages.success(request, "Fee marked as paid.")

        return redirect('accounts_student_detail', student_id=student.id)

    fees = StudentFee.objects.filter(
        student=student
    ).select_related(
        'fee_type'
    ).order_by('-id')

    payments = Payment.objects.filter(
        student=student
    ).order_by('-payment_date', '-id')

    waivers = Waiver.objects.filter(
        student=student
    ).order_by('-created_at')

    fee_types = FeeType.objects.all().order_by('name')

    total_payable = fees.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_waiver = waivers.aggregate(total=Sum('amount'))['total'] or 0

    balance = total_payable - total_paid - total_waiver

    if balance > 0:
        current_due = balance
        credit_balance = 0
    else:
        current_due = 0
        credit_balance = abs(balance)

    context = {
        'student': student,
        'fees': fees,
        'payments': payments,
        'waivers': waivers,
        'fee_types': fee_types,

        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_waiver': total_waiver,
        'current_due': current_due,
        'credit_balance': credit_balance,
    }

    return render(request, 'dashboard/accounts_student_detail.html', context)


@login_required
def delete_student_fee(request, fee_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    fee = get_object_or_404(
        StudentFee.objects.select_related('student'),
        id=fee_id
    )

    student_id = fee.student.id

    if request.method == 'POST':
        fee.delete()
        messages.success(request, "Payable fee deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('accounts_student_detail', student_id=student_id)


@login_required
def delete_payment(request, payment_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    payment = get_object_or_404(
        Payment.objects.select_related('student'),
        id=payment_id
    )

    student_id = payment.student.id

    if request.method == 'POST':
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('accounts_student_detail', student_id=student_id)


@login_required
def delete_waiver(request, waiver_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    waiver = get_object_or_404(
        Waiver.objects.select_related('student'),
        id=waiver_id
    )

    student_id = waiver.student.id

    if request.method == 'POST':
        waiver.delete()
        messages.success(request, "Waiver deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('accounts_student_detail', student_id=student_id)


@login_required
def download_payment_receipt(request, payment_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    payment = get_object_or_404(
        Payment.objects.select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester'
        ),
        id=payment_id
    )

    student = payment.student

    total_payable = StudentFee.objects.filter(
        student=student
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_paid = Payment.objects.filter(
        student=student
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_waiver = Waiver.objects.filter(
        student=student
    ).aggregate(total=Sum('amount'))['total'] or 0

    balance = total_payable - total_paid - total_waiver

    if balance > 0:
        current_due = balance
        credit_balance = 0
    else:
        current_due = 0
        credit_balance = abs(balance)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_Receipt_{student.student_id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 60

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, y, "University of Global Village (UGV)")

    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Payment Receipt")

    y -= 50
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Receipt ID: {payment.id}")

    y -= 22
    p.drawString(60, y, f"Student Name: {student.user.get_full_name() or student.user.username}")

    y -= 22
    p.drawString(60, y, f"Student ID: {student.student_id}")

    y -= 22
    p.drawString(60, y, f"Department: {student.department}")

    y -= 22
    p.drawString(60, y, f"Batch: {student.batch}")

    y -= 22
    p.drawString(60, y, f"Semester: {student.current_semester}")

    y -= 35
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y, "Payment Information")

    y -= 25
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Payment Date: {payment.payment_date}")

    y -= 22
    p.drawString(60, y, f"Amount Paid: {payment.amount} BDT")

    y -= 22
    p.drawString(60, y, f"Received By: {payment.received_by}")

    y -= 22
    p.drawString(60, y, f"Note: {payment.note or 'N/A'}")

    y -= 35
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y, "Account Summary")

    y -= 25
    p.setFont("Helvetica", 11)
    p.drawString(60, y, f"Total Payable: {total_payable} BDT")

    y -= 22
    p.drawString(60, y, f"Total Paid: {total_paid} BDT")

    y -= 22
    p.drawString(60, y, f"Total Waiver: {total_waiver} BDT")

    y -= 22
    p.drawString(60, y, f"Current Due: {current_due} BDT")

    y -= 22
    p.drawString(60, y, f"Credit Balance: {credit_balance} BDT")

    y -= 60
    p.drawString(60, y, "Student Signature")
    p.drawString(380, y, "Accounts Officer Signature")

    y -= 10
    p.line(60, y, 170, y)
    p.line(380, y, 530, y)

    p.showPage()
    p.save()

    return response


@login_required
def exam_controller_dashboard(request):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    selected_department_id = request.GET.get('department')

    departments = Department.objects.all().order_by('name')

    course_offerings_query = CourseOffering.objects.select_related(
        'course',
        'batch',
        'semester',
        'faculty'
    )

    students_query = StudentProfile.objects.select_related(
        'user',
        'department',
        'batch',
        'current_semester'
    )

    faculty_users = User.objects.filter(
        role='faculty'
    ).order_by('username')

    if selected_department_id:
        course_offerings_query = course_offerings_query.filter(
            Q(course__department_id=selected_department_id) |
            Q(batch__department_id=selected_department_id)
        )

        students_query = students_query.filter(
            department_id=selected_department_id
        )

    course_offerings = course_offerings_query.order_by(
        'semester__id',
        'course__code'
    )

    students = students_query.order_by('student_id')

    routines = ExamRoutine.objects.select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__batch',
        'course_offering__semester'
    )

    seat_plans = SeatPlan.objects.select_related(
        'student',
        'student__user',
        'course_offering',
        'course_offering__course'
    )

    hall_duties = HallDuty.objects.select_related(
        'faculty',
        'exam_routine',
        'exam_routine__course_offering',
        'exam_routine__course_offering__course'
    )

    result_publications = ResultPublication.objects.select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__batch',
        'course_offering__semester',
        'published_by'
    )

    if selected_department_id:
        routines = routines.filter(
            Q(course_offering__course__department_id=selected_department_id) |
            Q(course_offering__batch__department_id=selected_department_id)
        )

        seat_plans = seat_plans.filter(
            Q(course_offering__course__department_id=selected_department_id) |
            Q(course_offering__batch__department_id=selected_department_id)
        )

        hall_duties = hall_duties.filter(
            Q(exam_routine__course_offering__course__department_id=selected_department_id) |
            Q(exam_routine__course_offering__batch__department_id=selected_department_id)
        )

        result_publications = result_publications.filter(
            Q(course_offering__course__department_id=selected_department_id) |
            Q(course_offering__batch__department_id=selected_department_id)
        )

    routines = routines.order_by('-exam_date', '-id')

    seat_plans = seat_plans.order_by(
        'course_offering__course__code',
        'student__student_id'
    )

    hall_duties = hall_duties.order_by('-id')

    result_publications = result_publications.order_by(
        'course_offering__semester__id',
        'course_offering__course__code',
        'exam_type'
    )

    semesters = []
    used_semester_ids = set()

    for offering in course_offerings:
        if offering.semester and offering.semester.id not in used_semester_ids:
            semesters.append(offering.semester)
            used_semester_ids.add(offering.semester.id)

    def redirect_exam_dashboard():
        posted_department_id = request.POST.get('selected_department_id')

        if posted_department_id:
            return redirect(f'/exam-controller/?department={posted_department_id}')

        return redirect('exam_controller_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_routine':
            course_offering_id = request.POST.get('course_offering')
            exam_type = request.POST.get('exam_type')
            exam_date = request.POST.get('exam_date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            room = request.POST.get('room')
            is_published = request.POST.get('is_published') == 'on'

            course_offering = CourseOffering.objects.filter(
                id=course_offering_id
            ).first()

            if course_offering:
                routine, created = ExamRoutine.objects.update_or_create(
                    course_offering=course_offering,
                    exam_type=exam_type,
                    defaults={
                        'exam_date': exam_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'room': room,
                        'is_published': is_published,
                    }
                )

                if created:
                    messages.success(request, "Exam routine created successfully.")
                else:
                    messages.success(request, "Exam routine updated successfully.")
            else:
                messages.error(request, "Invalid course offering selected.")

            return redirect_exam_dashboard()

        elif action == 'toggle_routine':
            routine_id = request.POST.get('routine_id')
            routine = ExamRoutine.objects.filter(id=routine_id).first()

            if routine:
                routine.is_published = not routine.is_published
                routine.save()

                if routine.is_published:
                    messages.success(request, "Exam routine published.")
                else:
                    messages.warning(request, "Exam routine unpublished.")
            else:
                messages.error(request, "Exam routine not found.")

            return redirect_exam_dashboard()

        elif action == 'create_seat_plan':
            student_id = request.POST.get('student')
            course_offering_id = request.POST.get('course_offering')
            exam_type = request.POST.get('exam_type')
            room = request.POST.get('room')
            seat_number = request.POST.get('seat_number')
            is_published = request.POST.get('is_published') == 'on'

            student = StudentProfile.objects.filter(id=student_id).first()

            course_offering = CourseOffering.objects.filter(
                id=course_offering_id
            ).first()

            if student and course_offering:
                seat_plan, created = SeatPlan.objects.update_or_create(
                    student=student,
                    course_offering=course_offering,
                    exam_type=exam_type,
                    defaults={
                        'room': room,
                        'seat_number': seat_number,
                        'is_published': is_published,
                    }
                )

                if created:
                    messages.success(request, "Seat plan created successfully.")
                else:
                    messages.success(request, "Seat plan updated successfully.")
            else:
                messages.error(request, "Invalid student or course offering selected.")

            return redirect_exam_dashboard()

        elif action == 'toggle_seat_plan':
            seat_plan_id = request.POST.get('seat_plan_id')
            seat_plan = SeatPlan.objects.filter(id=seat_plan_id).first()

            if seat_plan:
                seat_plan.is_published = not seat_plan.is_published
                seat_plan.save()

                if seat_plan.is_published:
                    messages.success(request, "Seat plan published.")
                else:
                    messages.warning(request, "Seat plan unpublished.")
            else:
                messages.error(request, "Seat plan not found.")

            return redirect_exam_dashboard()

        elif action == 'assign_hall_duty':
            faculty_id = request.POST.get('faculty')
            exam_routine_id = request.POST.get('exam_routine')
            duty_room = request.POST.get('duty_room')
            duty_note = request.POST.get('duty_note')

            faculty = User.objects.filter(
                id=faculty_id,
                role='faculty'
            ).first()

            exam_routine = ExamRoutine.objects.filter(
                id=exam_routine_id
            ).first()

            if faculty and exam_routine:
                hall_duty, created = HallDuty.objects.update_or_create(
                    faculty=faculty,
                    exam_routine=exam_routine,
                    duty_room=duty_room,
                    defaults={
                        'duty_note': duty_note,
                    }
                )

                if created:
                    messages.success(request, "Hall duty assigned successfully.")
                else:
                    messages.success(request, "Hall duty updated successfully.")
            else:
                messages.error(request, "Invalid faculty or exam routine selected.")

            return redirect_exam_dashboard()

        elif action == 'unpublish_result':
            publication_id = request.POST.get('publication_id')

            publication = ResultPublication.objects.filter(
                id=publication_id
            ).first()

            if publication:
                publication.unpublish()
                messages.warning(request, "Result unpublished successfully.")
            else:
                messages.error(request, "Result publication record not found.")

            return redirect_exam_dashboard()

    context = {
        'departments': departments,
        'selected_department_id': selected_department_id,

        'course_offerings': course_offerings,
        'students': students,
        'faculty_users': faculty_users,
        'routines': routines,
        'seat_plans': seat_plans,
        'hall_duties': hall_duties,
        'result_publications': result_publications,
        'semesters': semesters,
    }

    return render(request, 'dashboard/exam_controller_dashboard.html', context)
@login_required
def exam_result_preview(request):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    course_offering_id = request.GET.get('course_offering')
    exam_type = request.GET.get('exam_type')

    if not course_offering_id or not exam_type:
        messages.error(request, "Please select course and exam type to preview result.")
        return redirect('exam_controller_dashboard')

    course_offering = get_object_or_404(
        CourseOffering.objects.select_related(
            'course',
            'batch',
            'semester',
            'faculty'
        ),
        id=course_offering_id
    )

    registrations = CourseRegistration.objects.filter(
        course_offering=course_offering,
        status='approved'
    ).select_related(
        'student',
        'student__user'
    ).order_by('student__student_id')

    result_rows = []

    for reg in registrations:
        student = reg.student

        mark = Mark.objects.filter(
            student=student,
            course_offering=course_offering,
            is_submitted=True
        ).first()

        midterm_total = 0

        if mark:
            midterm_total = (
                mark.class_test +
                mark.assignment +
                mark.attendance +
                mark.midterm
            )

        result_rows.append({
            'student': student,
            'mark': mark,
            'midterm_total': midterm_total,
        })

    publication = ResultPublication.objects.filter(
        course_offering=course_offering,
        exam_type=exam_type
    ).first()

    context = {
        'course_offering': course_offering,
        'exam_type': exam_type,
        'result_rows': result_rows,
        'publication': publication,
    }

    return render(request, 'dashboard/result_preview.html', context)


@login_required
def publish_result_from_preview(request):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('exam_controller_dashboard')

    course_offering_id = request.POST.get('course_offering')
    exam_type = request.POST.get('exam_type')

    course_offering = CourseOffering.objects.filter(
        id=course_offering_id
    ).first()

    if course_offering and exam_type:
        publication, created = ResultPublication.objects.get_or_create(
            course_offering=course_offering,
            exam_type=exam_type
        )

        publication.is_published = True
        publication.published_by = request.user
        publication.published_at = timezone.now()
        publication.save()

        messages.success(request, f"{exam_type.title()} result published successfully.")
    else:
        messages.error(request, "Invalid result publication request.")

    return redirect('exam_controller_dashboard')


@login_required
def download_semester_transcript(request):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    student_id = request.GET.get('student')
    semester_id = request.GET.get('semester')

    if not student_id or not semester_id:
        messages.error(request, "Please select student and semester.")
        return redirect('exam_controller_dashboard')

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'department',
            'batch',
            'current_semester'
        ),
        id=student_id
    )

    marks = Mark.objects.filter(
        student=student,
        is_submitted=True,
        course_offering__semester_id=semester_id,
        course_offering__resultpublication__exam_type='final',
        course_offering__resultpublication__is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course',
        'course_offering__semester'
    ).distinct().order_by(
        'course_offering__course__code'
    )

    if not marks:
        return HttpResponse("No published final result found for this student and semester.")

    semester = marks.first().course_offering.semester

    semester_total_credits = Decimal('0')
    semester_weighted_points = Decimal('0')

    for mark in marks:
        credit = Decimal(str(mark.course_offering.course.credit or 0))
        grade_point = Decimal(str(mark.grade_point or 0))

        semester_total_credits += credit
        semester_weighted_points += credit * grade_point

    if semester_total_credits > 0:
        semester_cgpa = round(semester_weighted_points / semester_total_credits, 2)
    else:
        semester_cgpa = 0

    all_final_marks = Mark.objects.filter(
        student=student,
        is_submitted=True,
        course_offering__resultpublication__exam_type='final',
        course_offering__resultpublication__is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course'
    ).distinct()

    total_credits = Decimal('0')
    total_weighted_points = Decimal('0')

    for mark in all_final_marks:
        credit = Decimal(str(mark.course_offering.course.credit or 0))
        grade_point = Decimal(str(mark.grade_point or 0))

        total_credits += credit
        total_weighted_points += credit * grade_point

    if total_credits > 0:
        overall_cgpa = round(total_weighted_points / total_credits, 2)
    else:
        overall_cgpa = 0

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_Transcript_{student.student_id}_{semester}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Watermark
    p.saveState()
    p.setFont("Helvetica-Bold", 55)
    p.setFillGray(0.90)
    p.translate(width / 2, height / 2)
    p.rotate(35)
    p.drawCentredString(0, 0, "UGV OFFICIAL")
    p.restoreState()

    y = height - 50

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, y, "University of Global Village (UGV)")

    y -= 25
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Official Semester Mark Sheet")

    y -= 30
    p.setFont("Helvetica", 10)
    p.drawCentredString(width / 2, y, "Issued by the Office of the Exam Controller")

    y -= 35
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Student Name: {student.user.get_full_name() or student.user.username}")
    p.drawString(330, y, f"Student ID: {student.student_id}")

    y -= 20
    p.drawString(50, y, f"Department: {student.department}")
    p.drawString(330, y, f"Batch: {student.batch}")

    y -= 20
    p.drawString(50, y, f"Semester: {semester}")
    p.drawString(330, y, f"Issue Date: {timezone.now().date()}")

    y -= 30

    p.setFont("Helvetica-Bold", 8)
    p.drawString(35, y, "Course Code")
    p.drawString(105, y, "Course Title")
    p.drawString(230, y, "Credit")
    p.drawString(270, y, "Quiz/CT")
    p.drawString(315, y, "Assign")
    p.drawString(360, y, "Attend")
    p.drawString(405, y, "Mid")
    p.drawString(445, y, "Final")
    p.drawString(485, y, "Grade")
    p.drawString(530, y, "GP")

    y -= 8
    p.line(35, y, 560, y)

    y -= 18
    p.setFont("Helvetica", 8)

    for mark in marks:
        if y < 130:
            p.showPage()

            p.saveState()
            p.setFont("Helvetica-Bold", 55)
            p.setFillGray(0.90)
            p.translate(width / 2, height / 2)
            p.rotate(35)
            p.drawCentredString(0, 0, "UGV OFFICIAL")
            p.restoreState()

            y = height - 60

        course = mark.course_offering.course

        p.drawString(35, y, str(course.code)[:12])
        p.drawString(105, y, str(course.title)[:20])
        p.drawString(230, y, str(course.credit))
        p.drawString(270, y, str(mark.class_test))
        p.drawString(315, y, str(mark.assignment))
        p.drawString(360, y, str(mark.attendance))
        p.drawString(405, y, str(mark.midterm))
        p.drawString(445, y, str(mark.final))
        p.drawString(485, y, str(mark.grade))
        p.drawString(530, y, str(mark.grade_point))

        y -= 18

    y -= 25
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, f"Semester Total Credits: {semester_total_credits}")
    p.drawString(330, y, f"Semester CGPA: {semester_cgpa}")

    y -= 22
    p.drawString(50, y, f"Overall Completed Credits: {total_credits}")
    p.drawString(330, y, f"Overall CGPA: {overall_cgpa}")

    y -= 45
    p.setFont("Helvetica", 9)
    p.drawString(50, y, "Prepared By")
    p.drawString(230, y, "Checked By")
    p.drawString(410, y, "Exam Controller")

    y -= 10
    p.line(50, y, 150, y)
    p.line(230, y, 330, y)
    p.line(410, y, 540, y)

    y -= 50
    p.setFont("Helvetica-Bold", 10)
    p.drawString(420, y, "Official Seal")

    p.circle(465, y - 35, 35)

    p.showPage()
    p.save()

    return response


@login_required
def edit_exam_routine(request, routine_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    routine = get_object_or_404(
        ExamRoutine.objects.select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__batch',
            'course_offering__semester'
        ),
        id=routine_id
    )

    course_offerings = CourseOffering.objects.filter(
        is_active=True
    ).select_related(
        'course',
        'batch',
        'semester'
    ).order_by('course__code')

    if request.method == 'POST':
        course_offering_id = request.POST.get('course_offering')
        exam_type = request.POST.get('exam_type')
        exam_date = request.POST.get('exam_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        room = request.POST.get('room')
        is_published = request.POST.get('is_published') == 'on'

        course_offering = CourseOffering.objects.filter(
            id=course_offering_id
        ).first()

        if course_offering and exam_type and exam_date and start_time and end_time and room:
            routine.course_offering = course_offering
            routine.exam_type = exam_type
            routine.exam_date = exam_date
            routine.start_time = start_time
            routine.end_time = end_time
            routine.room = room
            routine.is_published = is_published
            routine.save()

            messages.success(request, "Exam routine updated successfully.")
            return redirect('exam_controller_dashboard')
        else:
            messages.error(request, "Please fill all exam routine fields.")

    context = {
        'routine': routine,
        'course_offerings': course_offerings,
    }

    return render(request, 'dashboard/edit_exam_routine.html', context)


@login_required
def delete_exam_routine(request, routine_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    routine = get_object_or_404(ExamRoutine, id=routine_id)

    if request.method == 'POST':
        routine.delete()
        messages.success(request, "Exam routine deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('exam_controller_dashboard')


@login_required
def edit_seat_plan(request, seat_plan_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    seat_plan = get_object_or_404(
        SeatPlan.objects.select_related(
            'student',
            'student__user',
            'course_offering',
            'course_offering__course'
        ),
        id=seat_plan_id
    )

    students = StudentProfile.objects.select_related(
        'user',
        'department',
        'batch',
        'current_semester'
    ).order_by('student_id')

    course_offerings = CourseOffering.objects.filter(
        is_active=True
    ).select_related(
        'course',
        'batch',
        'semester'
    ).order_by('course__code')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        course_offering_id = request.POST.get('course_offering')
        exam_type = request.POST.get('exam_type')
        room = request.POST.get('room')
        seat_number = request.POST.get('seat_number')
        is_published = request.POST.get('is_published') == 'on'

        student = StudentProfile.objects.filter(id=student_id).first()
        course_offering = CourseOffering.objects.filter(
            id=course_offering_id
        ).first()

        if student and course_offering and exam_type and room and seat_number:
            seat_plan.student = student
            seat_plan.course_offering = course_offering
            seat_plan.exam_type = exam_type
            seat_plan.room = room
            seat_plan.seat_number = seat_number
            seat_plan.is_published = is_published
            seat_plan.save()

            messages.success(request, "Seat plan updated successfully.")
            return redirect('exam_controller_dashboard')
        else:
            messages.error(request, "Please fill all seat plan fields.")

    context = {
        'seat_plan': seat_plan,
        'students': students,
        'course_offerings': course_offerings,
    }

    return render(request, 'dashboard/edit_seat_plan.html', context)


@login_required
def delete_seat_plan(request, seat_plan_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    seat_plan = get_object_or_404(SeatPlan, id=seat_plan_id)

    if request.method == 'POST':
        seat_plan.delete()
        messages.success(request, "Seat plan deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('exam_controller_dashboard')


@login_required
def edit_hall_duty(request, hall_duty_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    hall_duty = get_object_or_404(
        HallDuty.objects.select_related(
            'faculty',
            'exam_routine',
            'exam_routine__course_offering',
            'exam_routine__course_offering__course'
        ),
        id=hall_duty_id
    )

    faculty_users = User.objects.filter(
        role='faculty',
        is_active=True
    ).order_by('username')

    routines = ExamRoutine.objects.select_related(
        'course_offering',
        'course_offering__course'
    ).order_by('-exam_date', 'start_time')

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        routine_id = request.POST.get('exam_routine')
        duty_room = request.POST.get('duty_room')
        duty_note = request.POST.get('duty_note')

        faculty = User.objects.filter(
            id=faculty_id,
            role='faculty'
        ).first()

        routine = ExamRoutine.objects.filter(
            id=routine_id
        ).first()

        if faculty and routine and duty_room:
            hall_duty.faculty = faculty
            hall_duty.exam_routine = routine
            hall_duty.duty_room = duty_room
            hall_duty.duty_note = duty_note
            hall_duty.save()

            messages.success(request, "Hall duty updated successfully.")
            return redirect('exam_controller_dashboard')
        else:
            messages.error(request, "Please select faculty, routine, and duty room.")

    context = {
        'hall_duty': hall_duty,
        'faculty_users': faculty_users,
        'routines': routines,
    }

    return render(request, 'dashboard/edit_hall_duty.html', context)


@login_required
def delete_hall_duty(request, hall_duty_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    hall_duty = get_object_or_404(HallDuty, id=hall_duty_id)

    if request.method == 'POST':
        hall_duty.delete()
        messages.success(request, "Hall duty deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('exam_controller_dashboard')


@login_required
def delete_result_publication(request, publication_id):
    if request.user.role != 'exam_controller':
        return redirect('dashboard')

    publication = get_object_or_404(ResultPublication, id=publication_id)

    if request.method == 'POST':
        publication.delete()
        messages.success(request, "Result publication deleted successfully.")
    else:
        messages.warning(request, "Invalid delete request.")

    return redirect('exam_controller_dashboard')


@login_required
def dept_head_dashboard(request):
    return render(request, 'dashboard/dept_head_dashboard.html')


@login_required
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html')


@login_required
def super_admin_dashboard(request):
    return render(request, 'dashboard/super_admin_dashboard.html')