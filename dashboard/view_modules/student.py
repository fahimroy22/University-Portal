from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from accounts.models import User
from academics.models import CourseMaterial
from students.models import StudentProfile, CourseRegistration
from finance.models import StudentFee, Payment, Waiver, StudentFinancialProfile
from faculty.models import (
    AttendanceSession,
    AttendanceRecord,
    Mark,
    Assignment,
    AssignmentSubmission,
)
from applications.models import StudentApplication
from exams.models import (
    ExamRoutine,
    SeatPlan,
    ResultPublication,
    StudentMarkReviewRequest,
)
from dashboard.view_modules.notices import get_notices_for_user


ZERO = Decimal('0.00')


def to_decimal(value):
    if value in [None, '']:
        return ZERO

    try:
        return Decimal(str(value))
    except Exception:
        return ZERO


def set_student_fee_display_values(fee):
    original_amount = getattr(fee, 'original_amount', None)
    waiver_amount = getattr(fee, 'waiver_amount', None)
    payable_amount = getattr(fee, 'amount', None)
    paid_amount = getattr(fee, 'paid_amount', None)

    fee.display_original_amount = to_decimal(original_amount or payable_amount)
    fee.display_waiver_amount = to_decimal(waiver_amount)
    fee.display_payable_amount = to_decimal(payable_amount)
    fee.display_paid_amount = to_decimal(paid_amount)

    if getattr(fee, 'is_paid', False) and fee.display_paid_amount <= ZERO:
        fee.display_paid_amount = fee.display_payable_amount

    fee.display_due_amount = fee.display_payable_amount - fee.display_paid_amount

    if fee.display_due_amount < ZERO:
        fee.display_due_amount = ZERO

    if getattr(fee, 'semester', None):
        fee.display_semester = str(fee.semester)
    else:
        fee.display_semester = 'Admission / One-time'

    if fee.display_due_amount <= ZERO:
        fee.display_payment_status = 'Paid'
        fee.display_status_class = 'badge-paid'
    elif fee.display_paid_amount > ZERO:
        fee.display_payment_status = 'Partial'
        fee.display_status_class = 'badge-partial'
    else:
        fee.display_payment_status = 'Unpaid'
        fee.display_status_class = 'badge-unpaid'

    return fee


def calculate_student_finance_summary(profile):
    student_fees = list(
        StudentFee.objects.filter(
            student=profile
        ).select_related(
            'fee_type',
            'semester'
        ).order_by('-id')
    )

    total_original_payable = ZERO
    total_fee_waiver = ZERO
    total_payable = ZERO
    total_fee_paid_amount = ZERO

    for fee in student_fees:
        set_student_fee_display_values(fee)

        total_original_payable += fee.display_original_amount
        total_fee_waiver += fee.display_waiver_amount
        total_payable += fee.display_payable_amount
        total_fee_paid_amount += fee.display_paid_amount

    payments = Payment.objects.filter(
        student=profile
    ).order_by('-payment_date', '-id')

    total_payment_records = to_decimal(
        payments.aggregate(total=Sum('amount'))['total']
    )

    total_paid = max(total_payment_records, total_fee_paid_amount)

    waivers = Waiver.objects.filter(
        student=profile
    ).select_related(
        'student_fee',
        'student_fee__fee_type'
    ).order_by('-created_at')

    total_manual_waiver = to_decimal(
        waivers.filter(
            student_fee__isnull=True
        ).aggregate(total=Sum('amount'))['total']
    )

    total_waiver = total_fee_waiver + total_manual_waiver

    if total_manual_waiver > ZERO:
        total_payable = total_payable - total_manual_waiver

    if total_payable < ZERO:
        total_payable = ZERO

    balance = total_payable - total_paid

    if balance > ZERO:
        current_due = balance
        credit_balance = ZERO
    else:
        current_due = ZERO
        credit_balance = abs(balance)

    due_fees = [
        fee for fee in student_fees
        if fee.display_due_amount > ZERO
    ]

    paid_fees = [
        fee for fee in student_fees
        if fee.display_due_amount <= ZERO
    ]

    return {
        'student_fees': student_fees,
        'due_fees': due_fees,
        'paid_fees': paid_fees,
        'payments': payments,
        'waivers': waivers,
        'total_original_payable': total_original_payable,
        'total_fee_waiver': total_fee_waiver,
        'total_manual_waiver': total_manual_waiver,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_waiver': total_waiver,
        'current_due': current_due,
        'credit_balance': credit_balance,
    }


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
    latest_notices = []

    financial_profile = None
    student_fees = []
    due_fees = []
    paid_fees = []
    payments = []
    waivers = []

    total_payable = ZERO
    total_paid = ZERO
    total_waiver = ZERO
    current_due = ZERO
    credit_balance = ZERO

    admit_payment_ok = False
    admit_attendance_ok = False
    admit_final_eligible = False
    average_attendance = 0

    overall_cgpa = 0
    total_result_credits = Decimal('0')
    total_weighted_points = Decimal('0')

    today_panel = {
        'next_exam': None,
        'pending_assignments_count': 0,
        'latest_notice': None,
        'latest_material': None,
        'lowest_attendance': None,
        'payment_status': 'Not available',
        'payment_message': 'Payment information is not available.',
        'attendance_status': 'Not available',
        'attendance_message': 'Attendance information is not available.',
        'admit_status': 'Not available',
        'admit_message': 'Admit card eligibility is not available.',
    }

    if user.role == 'student':
        profile = StudentProfile.objects.filter(user=user).first()
        latest_notices = get_notices_for_user(user)[:3]

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

            financial_profile = StudentFinancialProfile.objects.select_related(
                'program_fee'
            ).filter(
                student=profile
            ).first()

            finance_summary = calculate_student_finance_summary(profile)

            student_fees = finance_summary['student_fees']
            due_fees = finance_summary['due_fees']
            paid_fees = finance_summary['paid_fees']
            payments = finance_summary['payments']
            waivers = finance_summary['waivers']

            total_payable = finance_summary['total_payable']
            total_paid = finance_summary['total_paid']
            total_waiver = finance_summary['total_waiver']
            current_due = finance_summary['current_due']
            credit_balance = finance_summary['credit_balance']

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

            today = timezone.localdate()
            now = timezone.now()

            next_exam = exam_routines.filter(
                exam_date__gte=today
            ).order_by(
                'exam_date',
                'start_time'
            ).first()

            published_assignments = Assignment.objects.filter(
                course_offering_id__in=course_offering_ids,
                is_published=True
            )

            submitted_assignment_ids = AssignmentSubmission.objects.filter(
                student=profile,
                assignment__in=published_assignments
            ).values_list('assignment_id', flat=True)

            pending_assignments_count = published_assignments.filter(
                accepting_submissions=True,
                deadline__gte=now
            ).exclude(
                id__in=submitted_assignment_ids
            ).count()

            lowest_attendance = None

            if attendance_summary:
                attended_courses = [
                    item for item in attendance_summary
                    if item['total_classes'] > 0
                ]

                if attended_courses:
                    lowest_attendance = min(
                        attended_courses,
                        key=lambda item: item['attendance_percent']
                    )

            if current_due <= 0:
                payment_status = 'Clear'
                payment_message = 'No current due.'
            else:
                payment_status = 'Due'
                payment_message = f'{current_due} BDT due.'

            if average_attendance >= 60:
                attendance_status = 'Safe'
                attendance_message = f'Average attendance {average_attendance}%.'
            elif average_attendance > 0:
                attendance_status = 'Warning'
                attendance_message = f'Average attendance {average_attendance}%.'
            else:
                attendance_status = 'No Data'
                attendance_message = 'No attendance record yet.'

            if admit_final_eligible:
                admit_status = 'Eligible'
                admit_message = 'Admit card requirements met.'
            else:
                admit_status = 'Check'
                admit_message = 'Payment or attendance requirement pending.'

            today_panel = {
                'next_exam': next_exam,
                'pending_assignments_count': pending_assignments_count,
                'latest_notice': latest_notices[0] if latest_notices else None,
                'latest_material': course_materials.first() if course_materials else None,
                'lowest_attendance': lowest_attendance,
                'payment_status': payment_status,
                'payment_message': payment_message,
                'attendance_status': attendance_status,
                'attendance_message': attendance_message,
                'admit_status': admit_status,
                'admit_message': admit_message,
            }

    return {
        'profile': profile,
        'current_courses': current_courses,
        'course_materials': course_materials,
        'recent_applications': recent_applications,
        'exam_routines': exam_routines,
        'seat_plans': seat_plans,
        'latest_notices': latest_notices,

        'financial_profile': financial_profile,
        'student_fees': student_fees,
        'due_fees': due_fees,
        'paid_fees': paid_fees,
        'payments': payments,
        'waivers': waivers,

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

        'today_panel': today_panel,
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
def download_admit_card(request, exam_type='final'):
    if request.user.role != 'student':
        return redirect('dashboard')

    import os
    from django.conf import settings
    from django.core.exceptions import FieldError
    from reportlab.lib.pagesizes import A4

    data = calculate_student_dashboard_data(request.user)

    profile = data['profile']
    current_courses = data['current_courses']
    current_due = data['current_due']
    admit_final_eligible = data['admit_final_eligible']

    if not profile:
        return HttpResponse("Student profile not found.")

    if not admit_final_eligible:
        return HttpResponse(
            "You are not eligible to download the admit card. "
            "Please clear payment dues and meet attendance requirements."
        )

    exam_type = str(exam_type or '').lower().strip()

    if exam_type not in ['midterm', 'final']:
        exam_type = 'final'

    financial_profile = StudentFinancialProfile.objects.select_related(
        'program_fee'
    ).filter(student=profile).first()

    course_offering_ids = list(
        current_courses.values_list('course_offering_id', flat=True)
    )

    routines = ExamRoutine.objects.filter(
        course_offering_id__in=course_offering_ids,
        is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course'
    )

    try:
        routines = routines.filter(exam_type=exam_type)
    except FieldError:
        pass

    routines = routines.order_by('exam_date', 'start_time')

    seat_plans = SeatPlan.objects.filter(
        student=profile,
        course_offering_id__in=course_offering_ids,
        is_published=True
    ).select_related(
        'course_offering',
        'course_offering__course'
    )

    try:
        seat_plans = seat_plans.filter(exam_type=exam_type)
    except FieldError:
        pass

    seat_plan_by_offering = {
        seat_plan.course_offering_id: seat_plan
        for seat_plan in seat_plans
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_{exam_type.title()}_Admit_Card_{profile.student_id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'UGV-Logo-02.png')

    accent = (0.50, 0.11, 0.11)
    accent_dark = (0.30, 0.04, 0.04)
    navy = (0.05, 0.08, 0.16)
    muted = (0.38, 0.45, 0.55)
    border = (0.68, 0.72, 0.78)
    pale_red = (1.00, 0.96, 0.96)
    pale_blue = (0.98, 0.99, 1.00)
    gold = (0.76, 0.48, 0.12)

    page_left = 30
    page_right = width - 30
    page_top = height - 30
    page_bottom = 34

    margin = 42
    content_x = margin
    content_w = width - (2 * margin)

    def fit_text(text, max_width, font="Helvetica", size=8):
        text = str(text or "-").strip()

        if p.stringWidth(text, font, size) <= max_width:
            return text

        while len(text) > 3 and p.stringWidth(text + "...", font, size) > max_width:
            text = text[:-1]

        return text + "..."

    def get_student_photo_path(student_obj):
        photo_field = getattr(student_obj, 'photo', None)

        if photo_field:
            try:
                if hasattr(photo_field, 'path') and os.path.exists(photo_field.path):
                    return photo_field.path
            except Exception:
                return None

        return None

    def draw_label_value(x, y, label, value, value_width=165):
        p.setFillColorRGB(*muted)
        p.setFont("Helvetica-Bold", 8)
        p.drawString(x, y, label)

        p.setFillColorRGB(*navy)
        p.setFont("Helvetica-Bold", 8.7)
        p.drawString(x + 92, y, ":")
        p.drawString(x + 104, y, fit_text(value, value_width, "Helvetica-Bold", 8.7))

    # Page border
    p.setStrokeColorRGB(*border)
    p.setLineWidth(1)
    p.roundRect(
        page_left,
        page_bottom,
        page_right - page_left,
        page_top - page_bottom,
        8,
        stroke=1,
        fill=0
    )

    # Header
    header_x = page_left
    header_y = height - 122
    header_w = page_right - page_left
    header_h = 92

    p.setFillColorRGB(*pale_red)
    p.roundRect(header_x, header_y, header_w, header_h, 8, stroke=0, fill=1)

    logo_size = 52
    logo_x = header_x + 22
    logo_y = header_y + 21

    if os.path.exists(logo_path):
        p.drawImage(
            logo_path,
            logo_x,
            logo_y,
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
            mask='auto'
        )

    badge_w = 118
    badge_h = 20
    badge_x = page_right - badge_w - 16
    badge_y = header_y + header_h - badge_h - 10

    p.setFillColorRGB(*gold)
    p.roundRect(badge_x, badge_y, badge_w, badge_h, 5, stroke=0, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 8.5)
    p.drawCentredString(
        badge_x + badge_w / 2,
        badge_y + 6,
        "Govt. & UGC Approved"
    )

    title_x = logo_x + logo_size + 20
    title_y = header_y + 60

    p.setFillColorRGB(*accent)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(title_x, title_y, "UNIVERSITY OF GLOBAL VILLAGE (UGV)")

    p.setFont("Helvetica-Bold", 13)
    p.drawString(title_x, title_y - 19, "BARISHAL")

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica-Bold", 9.4)
    p.drawString(
        title_x,
        title_y - 36,
        "THE FIRST SKILL BASED HI-TECH UNIVERSITY IN BANGLADESH"
    )

    # Exam title
    exam_title = "Midterm Examination" if exam_type == "midterm" else "Final Examination"

    title_block_y = header_y - 42

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(width / 2, title_block_y, exam_title)

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, title_block_y - 25, "ADMIT CARD")

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.8)
    p.line(width / 2 - 54, title_block_y - 30, width / 2 + 54, title_block_y - 30)

    # Student photo box
    photo_w = 68
    photo_h = 78
    photo_x = page_right - photo_w - 42
    photo_y = 590

    p.setFillColorRGB(0.98, 0.98, 0.98)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(photo_x, photo_y, photo_w, photo_h, 5, stroke=1, fill=1)

    photo_path = get_student_photo_path(profile)

    if photo_path:
        try:
            p.drawImage(
                photo_path,
                photo_x + 3,
                photo_y + 3,
                width=photo_w - 6,
                height=photo_h - 6,
                preserveAspectRatio=True,
                anchor='c',
                mask='auto'
            )
        except Exception:
            p.setFillColorRGB(*muted)
            p.setFont("Helvetica-Bold", 8)
            p.drawCentredString(photo_x + photo_w / 2, photo_y + 43, "Student")
            p.drawCentredString(photo_x + photo_w / 2, photo_y + 31, "Photo")
    else:
        p.setFillColorRGB(*muted)
        p.setFont("Helvetica-Bold", 8)
        p.drawCentredString(photo_x + photo_w / 2, photo_y + 43, "Student")
        p.drawCentredString(photo_x + photo_w / 2, photo_y + 31, "Photo")

    # Barcode
    barcode_x = photo_x + 9
    barcode_y = photo_y - 24

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.55)

    for i in range(22):
        line_x = barcode_x + (i * 2.1)
        line_h = 15 if i % 3 == 0 else 10
        p.line(line_x, barcode_y, line_x, barcode_y + line_h)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 6.5)
    p.drawCentredString(photo_x + photo_w / 2, barcode_y - 8, f"*{profile.student_id}*")

    # Student information box
    info_x = content_x
    info_y = 475
    info_w = content_w
    info_h = 106

    p.setFillColorRGB(1, 1, 1)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(info_x, info_y, info_w, info_h, 8, stroke=1, fill=1)

    program_name = financial_profile.program_fee.program_name if financial_profile else "N/A"
    student_name = profile.user.get_full_name() or profile.user.username
    payment_status = "Clear" if current_due <= ZERO else "Due Available"

    left_x = info_x + 18
    right_x = info_x + 302

    row_y = info_y + 78

    draw_label_value(left_x, row_y, "Program", program_name, 170)
    draw_label_value(right_x, row_y, "Student ID", profile.student_id, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Name", student_name, 170)
    draw_label_value(right_x, row_y, "Department", profile.department, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Batch / Session", profile.batch, 170)
    draw_label_value(right_x, row_y, "Semester", profile.current_semester, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Payment Status", payment_status, 170)
    draw_label_value(right_x, row_y, "Section", getattr(profile, 'section', 'A') or 'A', 130)

    # Routine table
    table_x = content_x
    table_top_y = 435
    table_w = content_w

    col_widths = [30, 78, 198, 72, 78, 48]
    col_positions = [table_x]

    for col_width in col_widths[:-1]:
        col_positions.append(col_positions[-1] + col_width)

    header_h = 24
    row_h = 23

    p.setFillColorRGB(*accent_dark)
    p.roundRect(table_x, table_top_y, table_w, header_h, 4, stroke=0, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 7.4)

    headers = ["Srl.", "Subject Code", "Subject Title", "Exam Date", "Exam Time", "Room"]

    for i, header in enumerate(headers):
        x = col_positions[i]
        w = col_widths[i]

        if i == 0:
            p.drawCentredString(x + w / 2, table_top_y + 8, header)
        else:
            p.drawString(x + 4, table_top_y + 8, header)

    current_y = table_top_y

    if routines:
        for index, routine in enumerate(routines, start=1):
            if index > 9:
                break

            current_y -= row_h

            if index % 2 == 0:
                p.setFillColorRGB(*pale_blue)
                p.rect(table_x, current_y, table_w, row_h, stroke=0, fill=1)

            p.setStrokeColorRGB(*border)
            p.setLineWidth(0.55)
            p.rect(table_x, current_y, table_w, row_h, stroke=1, fill=0)

            for x in col_positions[1:]:
                p.line(x, current_y, x, current_y + row_h)

            course = getattr(routine.course_offering, 'course', None)
            course_code = getattr(course, 'code', '-')
            course_title = getattr(course, 'title', '-')

            seat_plan = seat_plan_by_offering.get(getattr(routine, 'course_offering_id', None))

            room_text = "-"
            if seat_plan:
                room = getattr(seat_plan, 'room', None)
                seat_no = getattr(seat_plan, 'seat_number', None)

                if room and seat_no:
                    room_text = f"{room}/{seat_no}"
                elif room:
                    room_text = str(room)
                elif seat_no:
                    room_text = str(seat_no)

            start_time = getattr(routine, 'start_time', '')
            end_time = getattr(routine, 'end_time', '')
            exam_time = f"{start_time} - {end_time}"

            values = [
                str(index),
                course_code,
                course_title,
                getattr(routine, 'exam_date', '-'),
                exam_time,
                room_text,
            ]

            p.setFillColorRGB(*navy)
            p.setFont("Helvetica", 7.1)

            for i, value in enumerate(values):
                x = col_positions[i]
                w = col_widths[i]

                if i == 0:
                    p.drawCentredString(x + w / 2, current_y + 8, str(value))
                else:
                    p.drawString(
                        x + 4,
                        current_y + 8,
                        fit_text(value, w - 8, "Helvetica", 7.1)
                    )

    else:
        current_y -= row_h

        p.setStrokeColorRGB(*border)
        p.rect(table_x, current_y, table_w, row_h, stroke=1, fill=0)

        p.setFillColorRGB(*muted)
        p.setFont("Helvetica-Bold", 8.5)
        p.drawCentredString(width / 2, current_y + 8, "No published exam routine found for this student.")

    # Important note
    note_y = current_y - 28

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 8.7)
    p.drawString(
        margin,
        note_y,
        "*Please sit in your designated seat; otherwise you may be marked absent for that exam."
    )

    # Instructions box
    instruction_y = 128
    instruction_w = content_w * 0.62
    instruction_h = 68

    p.setFillColorRGB(*pale_red)
    p.setStrokeColorRGB(*border)
    p.roundRect(margin, instruction_y, instruction_w, instruction_h, 7, stroke=1, fill=1)

    p.setFillColorRGB(*accent_dark)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(margin + 12, instruction_y + 50, "Instructions")

    instructions = [
        "1. Bring this admit card to the examination hall.",
        "2. Sign the attendance sheet for each examination.",
        "3. Report 30 minutes before start time.",
        "4. Sit in your designated seat only.",
    ]

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica", 7.4)

    inst_y = instruction_y + 36

    for line in instructions:
        p.drawString(margin + 12, inst_y, line)
        inst_y -= 11

    # Signature
    sign_x = width - margin - 170
    sign_y = instruction_y + 35

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.8)
    p.line(sign_x, sign_y, sign_x + 150, sign_y)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(sign_x + 75, sign_y - 14, "Controller of Examination")

    # Footer
    p.setFillColorRGB(*muted)
    p.setFont("Helvetica", 7)
    p.drawString(margin, 64, f"Printed by: {request.user.username}")
    p.drawString(margin, 51, "Automatically Software Generated Admit Card")

    p.drawRightString(width - margin, 64, "874/322, C&B Road, Barishal, Bangladesh")
    p.drawRightString(width - margin, 51, "Email: info@ugv.edu.bd | Tel: 0341-61521")

    # Bottom color strip
    p.setFillColorRGB(*gold)
    p.rect(page_left, page_bottom, page_right - page_left, 6, stroke=0, fill=1)

    p.setFillColorRGB(*accent)
    p.rect(page_left, page_bottom + 6, page_right - page_left, 4, stroke=0, fill=1)

    p.showPage()
    p.save()

    return response

@login_required
def student_profile_page(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    # Reuse the same calculated academic/result data used by
    # the dashboard and results page.
    context = calculate_student_dashboard_data(request.user)

    profile = context.get('profile')

    if not profile:
        return HttpResponse("Student profile not found.")

    # ---------------------------------------------------------
    # CURRENT SEMESTER REGISTRATIONS
    # ---------------------------------------------------------
    current_registrations = list(
        CourseRegistration.objects.filter(
            student=profile,
            status='approved',
            course_offering__semester=profile.current_semester
        ).select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__semester',
            'course_offering__batch',
        ).order_by(
            'course_offering__course__code'
        )
    )

    # ---------------------------------------------------------
    # CURRENT SECTION
    #
    # Section belongs to CourseOffering, not StudentProfile.
    # Collect all unique section values from current-semester
    # approved course registrations.
    # ---------------------------------------------------------
    current_sections = []

    for registration in current_registrations:
        section = (
            registration.course_offering.section
            or ''
        ).strip()

        if section and section not in current_sections:
            current_sections.append(section)

    if len(current_sections) == 1:
        current_section = current_sections[0]

    elif len(current_sections) > 1:
        # Supports students who may exceptionally have courses
        # assigned to more than one section.
        current_section = ', '.join(current_sections)

    else:
        current_section = 'Not assigned'

    # ---------------------------------------------------------
    # RESULT / CGPA
    #
    # Use the SAME dynamically calculated CGPA used by the
    # Results page. Do not use profile.cgpa for display.
    # ---------------------------------------------------------
    overall_cgpa = context.get('overall_cgpa', 0)
    total_result_credits = context.get(
        'total_result_credits',
        Decimal('0')
    )

    context.update({
        'current_registrations': current_registrations,
        'current_section': current_section,

        # Explicitly expose the same result values used by
        # the Results page.
        'profile_overall_cgpa': overall_cgpa,
        'profile_completed_credits': total_result_credits,
    })

    return render(
        request,
        'dashboard/student_profile.html',
        context
    )


@login_required
def student_courses_page(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.select_related(
        'department',
        'batch',
        'current_semester'
    ).filter(
        user=request.user
    ).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    # All approved course registrations for this student.
    all_course_registrations = list(
        CourseRegistration.objects.filter(
            student=profile,
            status='approved'
        ).select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__faculty',
            'course_offering__semester'
        ).order_by(
            'course_offering__course__code'
        )
    )

    current_semester = profile.current_semester

    # Current semester courses only.
    current_courses = [
        registration
        for registration in all_course_registrations
        if registration.course_offering.semester_id == profile.current_semester_id
    ]

    # Group all previous courses by semester.
    previous_semester_dict = {}

    for registration in all_course_registrations:
        semester = registration.course_offering.semester

        if not semester:
            continue

        # Skip the student's current semester.
        if semester.id == profile.current_semester_id:
            continue

        if semester.id not in previous_semester_dict:
            previous_semester_dict[semester.id] = {
                'semester': semester,
                'courses': [],
            }

        previous_semester_dict[semester.id]['courses'].append(registration)

    def get_semester_number(semester):
        """
        Extract a numeric semester order from names such as:
        '1st Semester'
        '2nd Semester'
        'Semester 3'
        '7th Semester'

        Falls back to the semester database ID if no number is found.
        """
        import re

        semester_name = str(semester.name or semester)

        match = re.search(r'\d+', semester_name)

        if match:
            return int(match.group())

        return semester.id

    # Previous semesters shown newest to oldest:
    # 6th, 5th, 4th ... 1st
    previous_semesters = sorted(
        previous_semester_dict.values(),
        key=lambda item: get_semester_number(item['semester']),
        reverse=True
    )

    context = {
        'profile': profile,
        'current_semester': current_semester,
        'current_courses': current_courses,
        'previous_semesters': previous_semesters,
        'total_approved_courses': len(all_course_registrations),
    }

    return render(
        request,
        'dashboard/student_courses.html',
        context
    )

@login_required
def student_course_summary_page(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.select_related(
        'department',
        'batch',
        'current_semester'
    ).filter(
        user=request.user
    ).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    current_registrations = list(
        CourseRegistration.objects.filter(
            student=profile,
            status='approved',
            course_offering__semester=profile.current_semester
        ).select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__faculty',
            'course_offering__semester'
        ).order_by(
            'course_offering__course__code'
        )
    )

    course_offering_ids = [
        registration.course_offering_id
        for registration in current_registrations
    ]

    marks_dict = {
        mark.course_offering_id: mark
        for mark in Mark.objects.filter(
            student=profile,
            course_offering_id__in=course_offering_ids,
            is_submitted=True
        ).select_related(
            'course_offering'
        )
    }

    course_summary_rows = []

    total_raw_marks = ZERO
    total_possible_marks = Decimal('150.00') * len(current_registrations)

    attendance_percentage_sum = Decimal('0.00')
    courses_with_attendance = 0

    for registration in current_registrations:
        course_offering = registration.course_offering
        course = course_offering.course

        total_classes = AttendanceSession.objects.filter(
            course_offering=course_offering
        ).count()

        present_classes = AttendanceRecord.objects.filter(
            student=profile,
            session__course_offering=course_offering,
            is_present=True
        ).count()

        if total_classes > 0:
            attendance_percentage = round(
                (present_classes / total_classes) * 100,
                2
            )

            attendance_percentage_sum += Decimal(
                str(attendance_percentage)
            )

            courses_with_attendance += 1
        else:
            attendance_percentage = 0

        mark = marks_dict.get(course_offering.id)

        if mark:
            class_test = mark.class_test
            assignment = mark.assignment
            attendance_mark = mark.attendance
            midterm = mark.midterm
            final_mark = mark.final
            raw_total = mark.raw_total
            normalized_total = mark.total
            grade = mark.grade or 'Pending'

            total_raw_marks += raw_total
        else:
            class_test = None
            assignment = None
            attendance_mark = None
            midterm = None
            final_mark = None
            raw_total = ZERO
            normalized_total = ZERO
            grade = 'Pending'

        faculty = course_offering.faculty

        if faculty:
            faculty_name = faculty.get_full_name() or faculty.username
        else:
            faculty_name = 'Not assigned'

        course_summary_rows.append({
            'registration': registration,
            'course_offering': course_offering,
            'course_code': course.code,
            'course_name': course.title,
            'credit': course.credit,
            'faculty_name': faculty_name,

            'total_classes': total_classes,
            'present_classes': present_classes,
            'attendance_percentage': attendance_percentage,

            'mark': mark,
            'class_test': class_test,
            'assignment': assignment,
            'attendance_mark': attendance_mark,
            'midterm': midterm,
            'final_mark': final_mark,

            'raw_total': raw_total,
            'normalized_total': normalized_total,
            'grade': grade,
        })

    if courses_with_attendance > 0:
        average_attendance = round(
            attendance_percentage_sum / courses_with_attendance,
            2
        )
    else:
        average_attendance = ZERO

    if total_possible_marks > ZERO:
        progress_percentage = round(
            (total_raw_marks / total_possible_marks) * Decimal('100'),
            2
        )
    else:
        progress_percentage = ZERO

    progress_percentage_float = float(progress_percentage)

    if progress_percentage_float >= 80:
        progress_status = 'Excellent'
    elif progress_percentage_float >= 60:
        progress_status = 'Good Progress'
    elif progress_percentage_float > 0:
        progress_status = 'In Progress'
    else:
        progress_status = 'Getting Started'

    context = {
        'profile': profile,
        'current_semester': profile.current_semester,
        'course_summary_rows': course_summary_rows,

        'total_courses': len(current_registrations),
        'average_attendance': average_attendance,

        'total_raw_marks': total_raw_marks,
        'total_possible_marks': total_possible_marks,
        'progress_percentage': progress_percentage,
        'progress_percentage_float': progress_percentage_float,
        'progress_status': progress_status,
    }

    return render(
        request,
        'dashboard/student_course_summary.html',
        context
    )

@login_required
def download_student_payment_receipt(request, payment_id):
    if request.user.role != 'student':
        return redirect('dashboard')

    import os
    from django.conf import settings
    from reportlab.lib.units import mm

    profile = StudentProfile.objects.filter(user=request.user).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    payment = get_object_or_404(
        Payment.objects.select_related(
            'student',
            'student__user',
            'student__department',
            'student__batch',
            'student__current_semester'
        ),
        id=payment_id,
        student=profile
    )

    student = profile

    financial_profile = StudentFinancialProfile.objects.select_related(
        'program_fee'
    ).filter(student=profile).first()

    receipt_width = 210 * mm
    receipt_height = 140 * mm

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_Receipt_{profile.student_id}_{payment.id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=(receipt_width, receipt_height))
    width, height = receipt_width, receipt_height

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'UGV-Logo-02.png')

    accent = (0.50, 0.11, 0.11)
    accent_dark = (0.28, 0.04, 0.04)
    navy = (0.05, 0.08, 0.16)
    muted = (0.39, 0.45, 0.55)
    border = (0.70, 0.75, 0.82)
    pale_red = (1.00, 0.965, 0.965)
    pale_blue = (0.975, 0.985, 1.00)

    margin = 10 * mm
    inner_w = width - (2 * margin)

    def fit_text(value, max_width, font="Helvetica", size=8):
        text = str(value or "-").strip()

        if p.stringWidth(text, font, size) <= max_width:
            return text

        while len(text) > 3 and p.stringWidth(text + "...", font, size) > max_width:
            text = text[:-1]

        return text + "..."

    def purpose_from_note(payment_obj):
        note = str(payment_obj.note or "").strip()
        note_lower = note.lower()

        if "semester fee" in note_lower:
            return "Semester Fee"
        if "admission fee" in note_lower:
            return "Admission Fee"
        if "exam fee" in note_lower:
            return "Exam Fee"
        if "library fee" in note_lower:
            return "Library Fee"
        if "lab fee" in note_lower:
            return "Lab Fee"
        if "payment for" in note_lower:
            cleaned = note.replace("Payment for", "").replace("payment for", "").strip()
            cleaned = cleaned.replace(".", "")
            return cleaned or "Payment Received"

        return note or "Payment Received"

    def draw_label_value(x, y, label, value, width_limit):
        p.setFillColorRGB(*muted)
        p.setFont("Helvetica-Bold", 6.8)
        p.drawString(x, y, label.upper())

        p.setFillColorRGB(*navy)
        p.setFont("Helvetica-Bold", 8.3)
        p.drawString(x, y - 4.2 * mm, fit_text(value, width_limit, "Helvetica-Bold", 8.3))

    # Main receipt border. Footer stays outside this border.
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(margin, 14 * mm, inner_w, height - margin - 14 * mm, 5, stroke=1, fill=0)

    # Header
    header_h = 24 * mm
    header_y = height - margin - header_h

    p.setFillColorRGB(*pale_red)
    p.roundRect(margin, header_y, inner_w, header_h, 5, stroke=0, fill=1)

    if os.path.exists(logo_path):
        logo_size = 16 * mm
        p.drawImage(
            logo_path,
            margin + 5 * mm,
            header_y + 4 * mm,
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
            mask='auto'
        )

    p.setFillColorRGB(*accent_dark)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin + 25 * mm, header_y + 15.2 * mm, "UNIVERSITY OF GLOBAL VILLAGE (UGV)")

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica-Bold", 7.8)
    p.drawString(margin + 25 * mm, header_y + 9.8 * mm, "Govt. & UGC Approved | Barishal, Bangladesh")

    p.setFillColorRGB(*accent)
    p.setFont("Helvetica-Bold", 8.8)
    p.drawString(margin + 25 * mm, header_y + 4.8 * mm, "Official Money Receipt")

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 7.8)
    p.drawRightString(width - margin - 5 * mm, header_y + 15.2 * mm, f"Receipt No: {payment.id}")
    p.drawRightString(width - margin - 5 * mm, header_y + 9.8 * mm, f"Date: {payment.payment_date}")
    p.drawRightString(width - margin - 5 * mm, header_y + 4.8 * mm, "Copy: Student")

    # Student information box
    student_box_x = margin + 5 * mm
    student_box_y = 78 * mm
    student_box_w = inner_w - 10 * mm
    student_box_h = 25 * mm

    p.setFillColorRGB(1, 1, 1)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.75)
    p.roundRect(student_box_x, student_box_y, student_box_w, student_box_h, 4, stroke=1, fill=1)

    student_name = student.user.get_full_name() or student.user.username
    program_name = financial_profile.program_fee.program_name if financial_profile else "N/A"

    col_1 = student_box_x + 6 * mm
    col_2 = student_box_x + 72 * mm
    col_3 = student_box_x + 138 * mm

    row_1 = student_box_y + 17 * mm
    row_2 = student_box_y + 7.5 * mm

    draw_label_value(col_1, row_1, "Student Name", student_name, 56 * mm)
    draw_label_value(col_2, row_1, "Student ID", student.student_id, 50 * mm)
    draw_label_value(col_3, row_1, "Department", student.department, 46 * mm)

    draw_label_value(col_1, row_2, "Program", program_name, 56 * mm)
    draw_label_value(col_2, row_2, "Batch / Session", student.batch, 50 * mm)
    draw_label_value(col_3, row_2, "Semester", student.current_semester, 46 * mm)

    # Payment details title
    title_y = 70 * mm

    p.setFillColorRGB(*accent)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(student_box_x, title_y, "Payment Details")

    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.55)
    p.line(student_box_x, title_y - 2.3 * mm, student_box_x + student_box_w, title_y - 2.3 * mm)

    # Payment table
    table_x = student_box_x
    table_y = 49 * mm
    table_w = student_box_w
    table_h = 17 * mm

    p.setFillColorRGB(1, 1, 1)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.75)
    p.roundRect(table_x, table_y, table_w, table_h, 4, stroke=1, fill=1)

    header_h = 7 * mm

    p.setFillColorRGB(*accent_dark)
    p.roundRect(table_x, table_y + table_h - header_h, table_w, header_h, 4, stroke=0, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 8.5)
    p.drawString(table_x + 5 * mm, table_y + table_h - 4.7 * mm, "Purpose of Payment")
    p.drawRightString(table_x + table_w - 5 * mm, table_y + table_h - 4.7 * mm, "Amount Paid")

    purpose = purpose_from_note(payment)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 9.2)
    p.drawString(table_x + 5 * mm, table_y + 5.5 * mm, fit_text(purpose, 125 * mm, "Helvetica-Bold", 9.2))
    p.drawRightString(table_x + table_w - 5 * mm, table_y + 5.5 * mm, f"{payment.amount} BDT")

    # Payment meta row
    meta_y = 42 * mm

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(table_x + 5 * mm, meta_y, f"Received By: {payment.received_by or '-'}")
    p.drawRightString(table_x + table_w - 5 * mm, meta_y, f"Payment Date: {payment.payment_date}")

    # Total amount row
    total_y = 33 * mm

    p.setFillColorRGB(*pale_blue)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.7)
    p.roundRect(table_x, total_y - 3 * mm, table_w, 8 * mm, 3, stroke=1, fill=1)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 9.5)
    p.drawString(table_x + 5 * mm, total_y, "Total Amount:")
    p.drawRightString(table_x + table_w - 5 * mm, total_y, f"{payment.amount} BDT")

    # Signature area - fully separated from footer
    sig_y = 22 * mm

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.75)
    p.line(table_x + 8 * mm, sig_y, table_x + 58 * mm, sig_y)
    p.line(table_x + table_w - 58 * mm, sig_y, table_x + table_w - 8 * mm, sig_y)

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica", 7)
    p.drawCentredString(table_x + 33 * mm, sig_y - 4 * mm, "Student Signature")
    p.drawCentredString(table_x + table_w - 33 * mm, sig_y - 4 * mm, "Accounts Officer Signature")

    # Footer outside the receipt box
    footer_y = 7 * mm

    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.45)
    p.line(margin + 5 * mm, footer_y + 4 * mm, width - margin - 5 * mm, footer_y + 4 * mm)

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica", 6.4)
    p.drawString(margin + 5 * mm, footer_y, "Email: info@ugv.edu.bd | ugvbarisal@gmail.com")
    p.drawCentredString(width / 2, footer_y, "874/322, C&B Road, Barishal")
    p.drawRightString(width - margin - 5 * mm, footer_y, "Tel: 0341-61521")

    p.showPage()
    p.save()

    return response
@login_required
def student_payments_page(request):
    context = calculate_student_dashboard_data(request.user)
    return render(request, 'dashboard/student_payments.html', context)


@login_required
def student_attendance_page(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    profile = StudentProfile.objects.select_related(
        'department',
        'batch',
        'current_semester'
    ).filter(
        user=request.user
    ).first()

    if not profile:
        return HttpResponse("Student profile not found.")

    current_registrations = list(
        CourseRegistration.objects.filter(
            student=profile,
            status='approved',
            course_offering__semester=profile.current_semester
        ).select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__faculty',
            'course_offering__semester'
        ).order_by(
            'course_offering__course__code'
        )
    )

    attendance_summary = []

    total_percentage = Decimal('0.00')
    courses_with_classes = 0

    total_classes_all_courses = 0
    total_present_all_courses = 0
    total_absent_all_courses = 0

    for registration in current_registrations:
        course_offering = registration.course_offering

        total_classes = AttendanceSession.objects.filter(
            course_offering=course_offering
        ).count()

        present_classes = AttendanceRecord.objects.filter(
            student=profile,
            session__course_offering=course_offering,
            is_present=True
        ).count()

        absent_classes = max(
            total_classes - present_classes,
            0
        )

        if total_classes > 0:
            attendance_percent = round(
                (present_classes / total_classes) * 100,
                2
            )

            total_percentage += Decimal(
                str(attendance_percent)
            )

            courses_with_classes += 1
        else:
            attendance_percent = 0

        total_classes_all_courses += total_classes
        total_present_all_courses += present_classes
        total_absent_all_courses += absent_classes

        faculty = course_offering.faculty

        if faculty:
            faculty_name = (
                faculty.get_full_name()
                or faculty.username
            )
        else:
            faculty_name = 'Not assigned'

        attendance_summary.append({
            'registration': registration,
            'course_offering': course_offering,
            'course_code': course_offering.course.code,
            'course_title': course_offering.course.title,
            'faculty_name': faculty_name,
            'total_classes': total_classes,
            'present_classes': present_classes,
            'absent_classes': absent_classes,
            'attendance_percent': attendance_percent,
        })

    if courses_with_classes > 0:
        average_attendance = round(
            total_percentage / courses_with_classes,
            2
        )
    else:
        average_attendance = Decimal('0.00')

    has_attendance_data = total_classes_all_courses > 0

    if not has_attendance_data:
        attendance_status = 'Pending'
        attendance_status_class = 'pending'
    elif average_attendance >= 60:
        attendance_status = 'Eligible'
        attendance_status_class = 'eligible'
    else:
        attendance_status = 'At Risk'
        attendance_status_class = 'risk'

    context = {
        'profile': profile,
        'current_semester': profile.current_semester,

        'attendance_summary': attendance_summary,
        'current_course_count': len(current_registrations),

        'average_attendance': average_attendance,
        'has_attendance_data': has_attendance_data,

        'attendance_status': attendance_status,
        'attendance_status_class': attendance_status_class,

        'attendance_requirement': 60,

        'total_classes_all_courses': total_classes_all_courses,
        'total_present_all_courses': total_present_all_courses,
        'total_absent_all_courses': total_absent_all_courses,
    }

    return render(
        request,
        'dashboard/student_attendance.html',
        context
    )

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
def student_mark_review_requests(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'department',
            'batch',
            'current_semester'
        ),
        user=request.user
    )

    review_requests = StudentMarkReviewRequest.objects.filter(
        student=student
    ).select_related(
        'mark',
        'course_offering',
        'course_offering__course',
        'course_offering__semester',
        'course_offering__faculty',
    ).order_by('-id')

    context = {
        'student': student,
        'review_requests': review_requests,
        'total_requests': review_requests.count(),
        'pending_count': review_requests.filter(
            status='pending_faculty'
        ).count(),
        'confirmed_count': review_requests.filter(
            status='faculty_confirmed'
        ).count(),
        'rejected_count': review_requests.filter(
            status='faculty_rejected'
        ).count(),
    }

    return render(
        request,
        'dashboard/student_mark_review_requests.html',
        context
    )


@login_required
def student_create_mark_review_request(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'department',
            'batch',
            'current_semester'
        ),
        user=request.user
    )

    # ---------------------------------------------------------
    # 1. Get all submitted marks for this student
    # ---------------------------------------------------------
    submitted_marks = (
        Mark.objects
        .filter(
            student=student,
            is_submitted=True
        )
        .select_related(
            'course_offering',
            'course_offering__course',
            'course_offering__semester',
            'course_offering__faculty',
            'course_offering__batch',
        )
        .order_by(
            '-course_offering__semester__number',
            'course_offering__course__code'
        )
    )

    # ---------------------------------------------------------
    # 2. Find course offerings that actually have
    #    published result records
    # ---------------------------------------------------------
    submitted_offering_ids = list(
        submitted_marks.values_list(
            'course_offering_id',
            flat=True
        )
    )

    published_results = (
        ResultPublication.objects
        .filter(
            course_offering_id__in=submitted_offering_ids,
            is_published=True
        )
        .select_related(
            'course_offering',
            'course_offering__semester'
        )
    )

    published_offering_ids = set(
        published_results.values_list(
            'course_offering_id',
            flat=True
        )
    )

    # ---------------------------------------------------------
    # 3. Keep only marks belonging to a published result
    # ---------------------------------------------------------
    available_marks = [
        mark
        for mark in submitted_marks
        if mark.course_offering_id in published_offering_ids
    ]

    # ---------------------------------------------------------
    # 4. Determine publication state for each mark
    #
    # This allows the template to know whether midterm,
    # final, or both result types are published.
    # ---------------------------------------------------------
    publication_lookup = {}

    for publication in published_results:
        offering_id = publication.course_offering_id

        if offering_id not in publication_lookup:
            publication_lookup[offering_id] = {
                'midterm_published': False,
                'final_published': False,
            }

        if publication.exam_type == 'midterm':
            publication_lookup[offering_id]['midterm_published'] = True

        elif publication.exam_type == 'final':
            publication_lookup[offering_id]['final_published'] = True

    for mark in available_marks:
        publication_state = publication_lookup.get(
            mark.course_offering_id,
            {}
        )

        mark.midterm_published = publication_state.get(
            'midterm_published',
            False
        )

        mark.final_published = publication_state.get(
            'final_published',
            False
        )

    # ---------------------------------------------------------
    # 5. Build semester dropdown from actual available results
    # ---------------------------------------------------------
    semester_options = []
    seen_semester_ids = set()

    for mark in available_marks:
        semester = mark.course_offering.semester

        if not semester:
            continue

        if semester.id in seen_semester_ids:
            continue

        seen_semester_ids.add(semester.id)
        semester_options.append(semester)

    # Sort newest semester first
    semester_options.sort(
        key=lambda semester: getattr(
            semester,
            'number',
            semester.id
        ),
        reverse=True
    )

    # ---------------------------------------------------------
    # 6. Handle submission
    # ---------------------------------------------------------
    if request.method == 'POST':
        mark_id = request.POST.get('mark')
        reason = request.POST.get(
            'reason',
            ''
        ).strip()

        attachment = request.FILES.get(
            'attachment'
        )

        requested_components = request.POST.getlist(
            'requested_components'
        )

        # ---------------------------------------------
        # Validate selected mark
        # ---------------------------------------------
        selected_mark = next(
            (
                mark
                for mark in available_marks
                if str(mark.id) == str(mark_id)
            ),
            None
        )

        if not selected_mark:
            messages.error(
                request,
                'Please select a valid published result.'
            )

            return redirect(
                'student_create_mark_review_request'
            )

        # ---------------------------------------------
        # Validate requested components
        # ---------------------------------------------
        valid_components = {
            'class_test',
            'assignment',
            'attendance',
            'midterm',
            'final',
        }

        requested_components = [
            component
            for component in requested_components
            if component in valid_components
        ]

        if not requested_components:
            messages.error(
                request,
                'Please select at least one mark component to review.'
            )

            return redirect(
                'student_create_mark_review_request'
            )

        if not reason:
            messages.error(
                request,
                'Please explain why you believe the recorded mark may be incorrect.'
            )

            return redirect(
                'student_create_mark_review_request'
            )

        # ---------------------------------------------
        # Final publication check
        # ---------------------------------------------
        is_published = ResultPublication.objects.filter(
            course_offering=selected_mark.course_offering,
            is_published=True
        ).exists()

        if not is_published:
            messages.error(
                request,
                'You can only request a review for a published result.'
            )

            return redirect(
                'student_create_mark_review_request'
            )

        # ---------------------------------------------
        # Prevent duplicate pending request
        # ---------------------------------------------
        pending_request = (
            StudentMarkReviewRequest.objects
            .filter(
                student=student,
                mark=selected_mark,
                status='pending_faculty'
            )
            .exists()
        )

        if pending_request:
            messages.warning(
                request,
                'You already have a pending faculty review request for this result.'
            )

            return redirect(
                'student_mark_review_requests'
            )

        # ---------------------------------------------
        # Create review request
        # ---------------------------------------------
        StudentMarkReviewRequest.objects.create(
            student=student,
            mark=selected_mark,
            course_offering=selected_mark.course_offering,
            reason=reason,
            requested_components=requested_components,
            attachment=attachment,
        )

        messages.success(
            request,
            'Your mark review request has been sent to the responsible faculty member.'
        )

        return redirect(
            'student_mark_review_requests'
        )

    # ---------------------------------------------------------
    # 7. Template context
    # ---------------------------------------------------------
    context = {
        'student': student,

        # Keep both names for compatibility with different
        # template versions.
        'marks': available_marks,
        'available_marks': available_marks,

        'semester_options': semester_options,
    }

    return render(
        request,
        'dashboard/student_create_mark_review_request.html',
        context
    )
@login_required
def download_student_result_pdf(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    data = calculate_student_dashboard_data(request.user)

    profile = data['profile']
    midterm_results = data['midterm_results']
    final_results = data['final_results']
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
def download_student_semester_result_pdf(request, semester_id):
    if request.user.role != 'student':
        return redirect('dashboard')

    data = calculate_student_dashboard_data(request.user)

    profile = data['profile']

    if not profile:
        return HttpResponse("Student profile not found.")

    semester_result = None

    for item in data['semester_results']:
        if item['semester'].id == semester_id:
            semester_result = item
            break

    if not semester_result:
        return HttpResponse("Published semester result not found.")

    semester = semester_result['semester']
    marks = semester_result['courses']
    semester_cgpa = semester_result['semester_cgpa']
    total_credits = semester_result['total_credits']

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_{semester.name}_Result_{profile.student_id}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 60

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(
        width / 2,
        y,
        "University of Global Village (UGV)"
    )

    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(
        width / 2,
        y,
        f"{semester.name} Final Result"
    )

    y -= 40

    p.setFont("Helvetica", 10)
    p.drawString(
        50,
        y,
        f"Name: {profile.user.get_full_name() or profile.user.username}"
    )

    y -= 18
    p.drawString(
        50,
        y,
        f"Student ID: {profile.student_id}"
    )

    y -= 18
    p.drawString(
        50,
        y,
        f"Department: {profile.department}"
    )

    y -= 18
    p.drawString(
        50,
        y,
        f"Semester: {semester}"
    )

    y -= 32

    # Table headers
    p.setFont("Helvetica-Bold", 8)

    p.drawString(35, y, "Course Code")
    p.drawString(130, y, "Course Title")
    p.drawString(330, y, "Credit")
    p.drawString(390, y, "Grade")
    p.drawString(455, y, "GPA")

    y -= 8
    p.line(35, y, 555, y)

    y -= 20

    p.setFont("Helvetica", 8)

    for mark in marks:
        if y < 100:
            p.showPage()
            y = height - 60

        course = mark.course_offering.course

        p.drawString(
            35,
            y,
            str(course.code)[:16]
        )

        p.drawString(
            130,
            y,
            str(course.title)[:35]
        )

        p.drawString(
            330,
            y,
            str(course.credit)
        )

        p.drawString(
            390,
            y,
            str(mark.grade)
        )

        p.drawString(
            455,
            y,
            str(mark.grade_point)
        )

        y -= 20

    y -= 20

    p.setFont("Helvetica-Bold", 10)

    p.drawString(
        50,
        y,
        f"Completed Credits: {total_credits}"
    )

    y -= 20

    p.drawString(
        50,
        y,
        f"Semester CGPA: {semester_cgpa}"
    )

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