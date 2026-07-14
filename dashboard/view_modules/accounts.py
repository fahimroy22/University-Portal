from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from academics.models import Department, Batch, Semester
from students.models import StudentProfile
from finance.models import (
    FeeType,
    StudentFee,
    Payment,
    Waiver,
    StudentFinancialProfile,
)


ZERO = Decimal('0.00')


def to_decimal(value):
    if value in [None, '']:
        return ZERO

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return ZERO


def get_fee_due_amount(fee):
    payable_amount = to_decimal(getattr(fee, 'amount', None))
    paid_amount = to_decimal(getattr(fee, 'paid_amount', None))

    if getattr(fee, 'is_paid', False) and paid_amount <= ZERO:
        paid_amount = payable_amount

    due_amount = payable_amount - paid_amount

    if due_amount < ZERO:
        return ZERO

    return due_amount


def set_fee_display_values(fee):
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

    fee.display_payment_label = (
        f'{fee.fee_type.name} | {fee.display_semester} | '
        f'Due: {fee.display_due_amount} BDT'
    )

    return fee


def calculate_student_account_summary(student):
    fees = StudentFee.objects.filter(student=student)

    total_original_payable = ZERO
    total_fee_waiver = ZERO
    total_payable_before_manual_waiver = ZERO
    total_fee_paid_amount = ZERO

    for fee in fees:
        original_amount = getattr(fee, 'original_amount', None)
        waiver_amount = getattr(fee, 'waiver_amount', None)
        payable_amount = to_decimal(getattr(fee, 'amount', None))
        paid_amount = to_decimal(getattr(fee, 'paid_amount', None))

        if getattr(fee, 'is_paid', False) and paid_amount <= ZERO:
            paid_amount = payable_amount

        if original_amount in [None, '']:
            original_amount = payable_amount

        total_original_payable += to_decimal(original_amount)
        total_fee_waiver += to_decimal(waiver_amount)
        total_payable_before_manual_waiver += payable_amount
        total_fee_paid_amount += paid_amount

    total_payment_records = to_decimal(
        Payment.objects.filter(student=student).aggregate(total=Sum('amount'))['total']
    )

    total_paid = max(total_payment_records, total_fee_paid_amount)

    total_manual_waiver = to_decimal(
        Waiver.objects.filter(
            student=student,
            student_fee__isnull=True
        ).aggregate(total=Sum('amount'))['total']
    )

    total_waiver = total_fee_waiver + total_manual_waiver
    total_payable = total_payable_before_manual_waiver - total_manual_waiver

    if total_payable < ZERO:
        total_payable = ZERO

    balance = total_payable - total_paid

    if balance > ZERO:
        current_due = balance
        credit_balance = ZERO
    else:
        current_due = ZERO
        credit_balance = abs(balance)

    return {
        'total_original_payable': total_original_payable,
        'total_fee_waiver': total_fee_waiver,
        'total_manual_waiver': total_manual_waiver,
        'total_waiver': total_waiver,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'current_due': current_due,
        'credit_balance': credit_balance,
    }


def build_semester_filter_options(fees):
    options = []
    seen_semester_ids = set()
    has_admission_fee = False

    for fee in fees:
        if getattr(fee, 'semester', None):
            semester_id = str(fee.semester.id)

            if semester_id not in seen_semester_ids:
                seen_semester_ids.add(semester_id)
                options.append({
                    'value': semester_id,
                    'label': str(fee.semester),
                })
        else:
            has_admission_fee = True

    if has_admission_fee:
        options.insert(0, {
            'value': 'admission',
            'label': 'Admission / One-time',
        })

    return options


def get_student_registered_course_offering_ids(student):
    model_paths = [
        ('academics.models', 'CourseEnrollment'),
        ('academics.models', 'StudentCourseEnrollment'),
        ('academics.models', 'CourseRegistration'),
        ('students.models', 'CourseEnrollment'),
        ('students.models', 'StudentCourseEnrollment'),
        ('students.models', 'CourseRegistration'),
    ]

    for module_path, model_name in model_paths:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model = getattr(module, model_name)

            queryset = model.objects.filter(student=student)

            if hasattr(model, 'status'):
                queryset = queryset.filter(status__in=['approved', 'enrolled', 'active'])

            if hasattr(model, 'course_offering'):
                return list(queryset.values_list('course_offering_id', flat=True))

            if hasattr(model, 'offering'):
                return list(queryset.values_list('offering_id', flat=True))

        except Exception:
            continue

    return []


def get_student_exam_routines(student, exam_type):
    try:
        from exams.models import ExamRoutine
    except Exception:
        return []

    course_offering_ids = get_student_registered_course_offering_ids(student)

    try:
        routines = ExamRoutine.objects.select_related(
            'course_offering',
            'course_offering__course'
        ).filter(
            exam_type__iexact=exam_type,
            is_published=True
        )

        if course_offering_ids:
            routines = routines.filter(course_offering_id__in=course_offering_ids)
        else:
            routines = routines.filter(course_offering__semester=student.current_semester)

        return list(
            routines.order_by(
                'exam_date',
                'start_time',
                'course_offering__course__code'
            )
        )

    except Exception:
        return []


def get_student_seat_plan_map(student, course_offering_ids):
    try:
        from exams.models import SeatPlan
    except Exception:
        return {}

    try:
        seat_plans = SeatPlan.objects.filter(
            student=student,
            is_published=True
        ).select_related(
            'course_offering',
            'course_offering__course'
        )

        if course_offering_ids:
            seat_plans = seat_plans.filter(course_offering_id__in=course_offering_ids)

        return {
            seat_plan.course_offering_id: seat_plan
            for seat_plan in seat_plans
        }

    except Exception:
        return {}


def get_accounts_base_filter_context():
    return {
        'departments': Department.objects.all().order_by('code', 'name'),
        'batches': Batch.objects.select_related('department').order_by(
            'department__code',
            'admission_year',
            'batch_name'
        ),
        'semesters': Semester.objects.all().order_by('id'),
    }


def filter_students_queryset(request):
    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department', '').strip()
    batch_id = request.GET.get('batch', '').strip()
    semester_id = request.GET.get('semester', '').strip()

    students = StudentProfile.objects.select_related(
        'user',
        'department',
        'batch',
        'current_semester'
    )

    if query:
        students = students.filter(
            Q(student_id__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )

    if department_id:
        students = students.filter(department_id=department_id)

    if batch_id:
        students = students.filter(batch_id=batch_id)

    if semester_id:
        students = students.filter(current_semester_id=semester_id)

    return students.distinct().order_by(
        'department__code',
        'batch__admission_year',
        'batch__batch_name',
        'student_id'
    )


def build_student_account_rows(students, payment_status='all'):
    rows = []

    for student in students:
        summary = calculate_student_account_summary(student)

        if summary['current_due'] <= ZERO:
            status = 'paid'
            status_label = 'Clear'
            status_class = 'badge-paid'
        elif summary['total_paid'] > ZERO:
            status = 'partial'
            status_label = 'Partial'
            status_class = 'badge-partial'
        else:
            status = 'due'
            status_label = 'Due'
            status_class = 'badge-unpaid'

        if payment_status == 'paid' and status != 'paid':
            continue

        if payment_status == 'due' and status == 'paid':
            continue

        if payment_status == 'partial' and status != 'partial':
            continue

        rows.append({
            'student': student,
            'summary': summary,
            'status': status,
            'status_label': status_label,
            'status_class': status_class,
        })

    return rows


@login_required
def accounts_dashboard(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()

    if query:
        matched_student = StudentProfile.objects.select_related(
            'user'
        ).filter(
            Q(student_id__iexact=query)
            | Q(user__username__iexact=query)
        ).first()

        if matched_student:
            return redirect('accounts_student_detail', student_id=matched_student.id)

        matched_students = StudentProfile.objects.filter(
            Q(student_id__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )

        if matched_students.count() == 1:
            return redirect(
                'accounts_student_detail',
                student_id=matched_students.first().id
            )

        if matched_students.exists():
            students_url = reverse('accounts_students')
            return redirect(f'{students_url}?q={query}')

        messages.error(request, 'No student found with this ID, username, or name.')
        return redirect('accounts_dashboard')

    all_students = StudentProfile.objects.all()

    total_students = all_students.count()
    total_payable = ZERO
    total_paid = ZERO
    total_due = ZERO
    total_credit = ZERO

    students_with_due = 0
    cleared_students = 0

    for student in all_students:
        summary = calculate_student_account_summary(student)

        total_payable += summary['total_payable']
        total_paid += summary['total_paid']
        total_due += summary['current_due']
        total_credit += summary['credit_balance']

        if summary['current_due'] > ZERO:
            students_with_due += 1
        else:
            cleared_students += 1

    recent_payments = Payment.objects.select_related(
        'student',
        'student__user',
        'student__department'
    ).order_by('-payment_date', '-id')[:8]

    context = {
        'query': query,

        'total_students': total_students,
        'total_payable': total_payable,
        'total_paid': total_paid,
        'total_due': total_due,
        'total_credit': total_credit,
        'students_with_due': students_with_due,
        'cleared_students': cleared_students,
        'recent_payments': recent_payments,
    }

    return render(request, 'dashboard/accounts_dashboard.html', context)


@login_required
def accounts_students(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    payment_status = request.GET.get('payment_status', 'all').strip() or 'all'

    students = filter_students_queryset(request)
    student_rows = build_student_account_rows(
        students,
        payment_status=payment_status
    )

    context = get_accounts_base_filter_context()
    context.update({
        'student_rows': student_rows,
        'query': request.GET.get('q', '').strip(),
        'selected_department_id': request.GET.get('department', '').strip(),
        'selected_batch_id': request.GET.get('batch', '').strip(),
        'selected_semester_id': request.GET.get('semester', '').strip(),
        'payment_status': payment_status,
    })

    return render(request, 'dashboard/accounts_students.html', context)


@login_required
def accounts_payments(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    payments = Payment.objects.select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    ).order_by('-payment_date', '-id')

    if query:
        payments = payments.filter(
            Q(student__student_id__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(note__icontains=query)
            | Q(received_by__icontains=query)
        )

    if department_id:
        payments = payments.filter(student__department_id=department_id)

    if date_from:
        payments = payments.filter(payment_date__gte=date_from)

    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    total_amount = to_decimal(payments.aggregate(total=Sum('amount'))['total'])

    context = get_accounts_base_filter_context()
    context.update({
        'payments': payments,
        'total_amount': total_amount,
        'query': query,
        'selected_department_id': department_id,
        'date_from': date_from,
        'date_to': date_to,
    })

    return render(request, 'dashboard/accounts_payments.html', context)


@login_required
def accounts_dues(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    students = filter_students_queryset(request)
    student_rows = build_student_account_rows(students, payment_status='due')

    total_due = ZERO

    for row in student_rows:
        total_due += row['summary']['current_due']

    context = get_accounts_base_filter_context()
    context.update({
        'student_rows': student_rows,
        'total_due': total_due,
        'query': request.GET.get('q', '').strip(),
        'selected_department_id': request.GET.get('department', '').strip(),
        'selected_batch_id': request.GET.get('batch', '').strip(),
        'selected_semester_id': request.GET.get('semester', '').strip(),
    })

    return render(request, 'dashboard/accounts_dues.html', context)


@login_required
def accounts_waivers(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department', '').strip()

    waivers = Waiver.objects.select_related(
        'student',
        'student__user',
        'student__department',
        'student_fee',
        'student_fee__fee_type'
    ).order_by('-created_at')

    if query:
        waivers = waivers.filter(
            Q(student__student_id__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(reason__icontains=query)
            | Q(approved_by__icontains=query)
        )

    if department_id:
        waivers = waivers.filter(student__department_id=department_id)

    total_waiver = to_decimal(waivers.aggregate(total=Sum('amount'))['total'])

    context = get_accounts_base_filter_context()
    context.update({
        'waivers': waivers,
        'total_waiver': total_waiver,
        'query': query,
        'selected_department_id': department_id,
    })

    return render(request, 'dashboard/accounts_waivers.html', context)


@login_required
def accounts_receipts(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department', '').strip()

    payments = Payment.objects.select_related(
        'student',
        'student__user',
        'student__department',
        'student__batch',
        'student__current_semester'
    ).order_by('-payment_date', '-id')

    if query:
        payments = payments.filter(
            Q(student__student_id__icontains=query)
            | Q(student__user__username__icontains=query)
            | Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(note__icontains=query)
        )

    if department_id:
        payments = payments.filter(student__department_id=department_id)

    context = get_accounts_base_filter_context()
    context.update({
        'payments': payments,
        'query': query,
        'selected_department_id': department_id,
    })

    return render(request, 'dashboard/accounts_receipts.html', context)


@login_required
def accounts_admit_cards(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    payment_status = request.GET.get('payment_status', 'all').strip() or 'all'

    students = filter_students_queryset(request)
    student_rows = build_student_account_rows(
        students,
        payment_status=payment_status
    )

    context = get_accounts_base_filter_context()
    context.update({
        'student_rows': student_rows,
        'query': request.GET.get('q', '').strip(),
        'selected_department_id': request.GET.get('department', '').strip(),
        'selected_batch_id': request.GET.get('batch', '').strip(),
        'selected_semester_id': request.GET.get('semester', '').strip(),
        'payment_status': payment_status,
    })

    return render(request, 'dashboard/accounts_admit_cards.html', context)


@login_required
def accounts_reports(request):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    departments = Department.objects.all().order_by('code', 'name')

    department_rows = []

    grand_students = 0
    grand_payable = ZERO
    grand_paid = ZERO
    grand_due = ZERO

    for department in departments:
        students = StudentProfile.objects.filter(
            department=department
        ).select_related(
            'user',
            'batch',
            'current_semester'
        )

        student_count = students.count()
        total_payable = ZERO
        total_paid = ZERO
        total_due = ZERO

        for student in students:
            summary = calculate_student_account_summary(student)
            total_payable += summary['total_payable']
            total_paid += summary['total_paid']
            total_due += summary['current_due']

        grand_students += student_count
        grand_payable += total_payable
        grand_paid += total_paid
        grand_due += total_due

        department_rows.append({
            'department': department,
            'student_count': student_count,
            'total_payable': total_payable,
            'total_paid': total_paid,
            'total_due': total_due,
        })

    context = {
        'department_rows': department_rows,
        'grand_students': grand_students,
        'grand_payable': grand_payable,
        'grand_paid': grand_paid,
        'grand_due': grand_due,
    }

    return render(request, 'dashboard/accounts_reports.html', context)


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
            amount = to_decimal(request.POST.get('amount') or '0')
            due_date = request.POST.get('due_date') or None

            fee_type = FeeType.objects.filter(id=fee_type_id).first()

            if fee_type and amount > ZERO:
                StudentFee.objects.create(
                    student=student,
                    fee_type=fee_type,
                    original_amount=amount,
                    waiver_amount=ZERO,
                    amount=amount,
                    paid_amount=ZERO,
                    due_date=due_date,
                    is_paid=False,
                    status='unpaid'
                )
                messages.success(request, "Payable fee added successfully.")
            else:
                messages.error(request, "Please select fee type and enter valid amount.")

        elif action == 'add_payment':
            amount = to_decimal(request.POST.get('amount') or '0')
            note = request.POST.get('note', '').strip()
            selected_fee_id = request.POST.get('student_fee')
            print_receipt = request.POST.get('print_receipt')

            selected_fee = None

            if selected_fee_id:
                selected_fee = StudentFee.objects.select_related(
                    'fee_type',
                    'semester'
                ).filter(
                    id=selected_fee_id,
                    student=student
                ).first()

            if amount > ZERO:
                final_note = note

                if selected_fee:
                    set_fee_display_values(selected_fee)

                    fee_note = (
                        f'Payment for {selected_fee.fee_type.name} '
                        f'({selected_fee.display_semester}).'
                    )

                    if final_note:
                        final_note = f'{fee_note} {final_note}'
                    else:
                        final_note = fee_note

                payment = Payment.objects.create(
                    student=student,
                    amount=amount,
                    received_by=request.user.username,
                    note=final_note
                )

                if selected_fee:
                    selected_fee_payable = to_decimal(selected_fee.amount)
                    selected_fee_paid = to_decimal(getattr(selected_fee, 'paid_amount', None))
                    selected_fee_paid += amount

                    selected_fee.paid_amount = selected_fee_paid

                    if selected_fee_paid >= selected_fee_payable:
                        selected_fee.is_paid = True
                        selected_fee.status = 'paid'
                    elif selected_fee_paid > ZERO:
                        selected_fee.is_paid = False
                        selected_fee.status = 'partial'
                    else:
                        selected_fee.is_paid = False
                        selected_fee.status = 'unpaid'

                    selected_fee.save()

                messages.success(request, "Payment added successfully.")

                if print_receipt == '1':
                    return redirect('download_payment_receipt', payment_id=payment.id)
            else:
                messages.error(request, "Please enter a valid payment amount.")

        elif action == 'add_waiver':
            amount = to_decimal(request.POST.get('amount') or '0')
            reason = request.POST.get('reason')

            if amount > ZERO and reason:
                Waiver.objects.create(
                    student=student,
                    amount=amount,
                    source='manual',
                    reason=reason,
                    approved_by=request.user.username
                )
                messages.success(request, "Waiver added successfully.")
            else:
                messages.error(request, "Please enter valid waiver amount and reason.")

        elif action == 'mark_fee_paid':
            fee_id = request.POST.get('fee_id')

            fee = StudentFee.objects.select_related(
                'fee_type',
                'semester'
            ).filter(
                id=fee_id,
                student=student
            ).first()

            if fee:
                set_fee_display_values(fee)

                amount_due = fee.display_due_amount
                fee_payable = to_decimal(fee.amount)

                if amount_due <= ZERO and not fee.is_paid:
                    amount_due = fee_payable

                if amount_due > ZERO:
                    Payment.objects.create(
                        student=student,
                        amount=amount_due,
                        received_by=request.user.username,
                        note=(
                            f'Payment for {fee.fee_type.name} '
                            f'({fee.display_semester}).'
                        )
                    )

                fee.paid_amount = fee_payable
                fee.is_paid = True
                fee.status = 'paid'
                fee.save()

                messages.success(request, "Fee marked as paid and payment record created.")

        return redirect('accounts_student_detail', student_id=student.id)

    fee_filter = request.GET.get('fee_filter', 'all')
    semester_filter = request.GET.get('semester_filter', 'all')

    all_fees = list(
        StudentFee.objects.filter(
            student=student
        ).select_related(
            'fee_type',
            'semester'
        ).order_by('-id')
    )

    for fee in all_fees:
        set_fee_display_values(fee)

    unpaid_fees = [
        fee for fee in all_fees
        if fee.display_due_amount > ZERO
    ]

    semester_filter_options = build_semester_filter_options(all_fees)

    fees = all_fees

    if fee_filter == 'due':
        fees = [
            fee for fee in fees
            if fee.display_due_amount > ZERO
        ]
    elif fee_filter == 'paid':
        fees = [
            fee for fee in fees
            if fee.display_due_amount <= ZERO
        ]

    if semester_filter == 'admission':
        fees = [
            fee for fee in fees
            if not getattr(fee, 'semester', None)
        ]
    elif semester_filter != 'all':
        fees = [
            fee for fee in fees
            if getattr(fee, 'semester', None)
            and str(fee.semester.id) == str(semester_filter)
        ]

    payments = Payment.objects.filter(
        student=student
    ).order_by('-payment_date', '-id')

    waivers = Waiver.objects.filter(
        student=student
    ).select_related(
        'student_fee',
        'student_fee__fee_type'
    ).order_by('-created_at')

    fee_types = FeeType.objects.all().order_by('name')

    financial_profile = StudentFinancialProfile.objects.select_related(
        'program_fee'
    ).filter(
        student=student
    ).first()

    account_summary = calculate_student_account_summary(student)

    context = {
        'student': student,
        'financial_profile': financial_profile,
        'fees': fees,
        'all_fees': all_fees,
        'unpaid_fees': unpaid_fees,
        'payments': payments,
        'waivers': waivers,
        'fee_types': fee_types,

        'fee_filter': fee_filter,
        'semester_filter': semester_filter,
        'semester_filter_options': semester_filter_options,

        'total_original_payable': account_summary['total_original_payable'],
        'total_fee_waiver': account_summary['total_fee_waiver'],
        'total_manual_waiver': account_summary['total_manual_waiver'],
        'total_payable': account_summary['total_payable'],
        'total_paid': account_summary['total_paid'],
        'total_waiver': account_summary['total_waiver'],
        'current_due': account_summary['current_due'],
        'credit_balance': account_summary['credit_balance'],
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

    messages.error(request, "Accounts officers are not allowed to delete payable fees.")
    return redirect('accounts_student_detail', student_id=fee.student.id)


@login_required
def delete_payment(request, payment_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    payment = get_object_or_404(
        Payment.objects.select_related('student'),
        id=payment_id
    )

    messages.error(request, "Accounts officers are not allowed to delete payment history.")
    return redirect('accounts_student_detail', student_id=payment.student.id)


@login_required
def delete_waiver(request, waiver_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    waiver = get_object_or_404(
        Waiver.objects.select_related('student'),
        id=waiver_id
    )

    messages.error(request, "Accounts officers are not allowed to delete waiver history.")
    return redirect('accounts_student_detail', student_id=waiver.student.id)


@login_required
def download_accounts_admit_card(request, student_id, exam_type):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    import os
    from django.conf import settings
    from reportlab.lib.pagesizes import A4

    student = get_object_or_404(
        StudentProfile.objects.select_related(
            'user',
            'department',
            'batch',
            'current_semester'
        ),
        id=student_id
    )

    exam_type = str(exam_type or '').lower().strip()

    if exam_type not in ['midterm', 'final', 'recovery']:
        exam_type = 'final'

    financial_profile = StudentFinancialProfile.objects.select_related(
        'program_fee'
    ).filter(student=student).first()

    account_summary = calculate_student_account_summary(student)

    course_offering_ids = get_student_registered_course_offering_ids(student)
    routines = get_student_exam_routines(student, exam_type)
    seat_plan_by_offering = get_student_seat_plan_map(student, course_offering_ids)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_{exam_type.title()}_Admit_Card_{student.student_id}.pdf"'
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

    if exam_type == "midterm":
        exam_title = "Midterm Examination"
    elif exam_type == "recovery":
        exam_title = "Recovery Examination"
    else:
        exam_title = "Final Examination"

    title_block_y = header_y - 42

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(width / 2, title_block_y, exam_title)

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, title_block_y - 25, "ADMIT CARD")

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.8)
    p.line(width / 2 - 54, title_block_y - 30, width / 2 + 54, title_block_y - 30)

    photo_w = 68
    photo_h = 78
    photo_x = page_right - photo_w - 42
    photo_y = 590

    p.setFillColorRGB(0.98, 0.98, 0.98)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(photo_x, photo_y, photo_w, photo_h, 5, stroke=1, fill=1)

    photo_path = get_student_photo_path(student)

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
    p.drawCentredString(photo_x + photo_w / 2, barcode_y - 8, f"*{student.student_id}*")

    info_x = content_x
    info_y = 475
    info_w = content_w
    info_h = 106

    p.setFillColorRGB(1, 1, 1)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(info_x, info_y, info_w, info_h, 8, stroke=1, fill=1)

    program_name = financial_profile.program_fee.program_name if financial_profile else "N/A"
    student_name = student.user.get_full_name() or student.user.username
    payment_status = "Clear" if account_summary['current_due'] <= ZERO else "Due Available"

    left_x = info_x + 18
    right_x = info_x + 302

    row_y = info_y + 78

    draw_label_value(left_x, row_y, "Program", program_name, 170)
    draw_label_value(right_x, row_y, "Student ID", student.student_id, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Name", student_name, 170)
    draw_label_value(right_x, row_y, "Department", student.department, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Batch / Session", student.batch, 170)
    draw_label_value(right_x, row_y, "Semester", student.current_semester, 130)

    row_y -= 22
    draw_label_value(left_x, row_y, "Payment Status", payment_status, 170)
    draw_label_value(right_x, row_y, "Section", getattr(student, 'section', 'A') or 'A', 130)

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

    note_y = current_y - 28

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 8.7)
    p.drawString(
        margin,
        note_y,
        "*Please sit in your designated seat; otherwise you may be marked absent for that exam."
    )

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

    sign_x = width - margin - 170
    sign_y = instruction_y + 35

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.8)
    p.line(sign_x, sign_y, sign_x + 150, sign_y)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(sign_x + 75, sign_y - 14, "Controller of Examination")

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica", 7)
    p.drawString(margin, 64, f"Printed by: {request.user.username}")
    p.drawString(margin, 51, "Automatically Software Generated Admit Card")

    p.drawRightString(width - margin, 64, "874/322, C&B Road, Barishal, Bangladesh")
    p.drawRightString(width - margin, 51, "Email: info@ugv.edu.bd | Tel: 0341-61521")

    p.setFillColorRGB(*gold)
    p.rect(page_left, page_bottom, page_right - page_left, 6, stroke=0, fill=1)

    p.setFillColorRGB(*accent)
    p.rect(page_left, page_bottom + 6, page_right - page_left, 4, stroke=0, fill=1)

    p.showPage()
    p.save()

    return response


@login_required
def download_payment_receipt(request, payment_id):
    if request.user.role != 'accounts':
        return redirect('dashboard')

    import os
    from django.conf import settings

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

    financial_profile = StudentFinancialProfile.objects.select_related(
        'program_fee'
    ).filter(student=student).first()

    receipt_width = 210 * mm
    receipt_height = 140 * mm

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="UGV_Receipt_{student.student_id}_{payment.id}.pdf"'
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

    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.9)
    p.roundRect(margin, 14 * mm, inner_w, height - margin - 14 * mm, 5, stroke=1, fill=0)

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
    p.drawRightString(width - margin - 5 * mm, header_y + 4.8 * mm, "Copy: Accounts / Student")

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

    title_y = 70 * mm

    p.setFillColorRGB(*accent)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(student_box_x, title_y, "Payment Details")

    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.55)
    p.line(student_box_x, title_y - 2.3 * mm, student_box_x + student_box_w, title_y - 2.3 * mm)

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

    meta_y = 42 * mm

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(table_x + 5 * mm, meta_y, f"Received By: {payment.received_by or '-'}")
    p.drawRightString(table_x + table_w - 5 * mm, meta_y, f"Payment Date: {payment.payment_date}")

    total_y = 33 * mm

    p.setFillColorRGB(*pale_blue)
    p.setStrokeColorRGB(*border)
    p.setLineWidth(0.7)
    p.roundRect(table_x, total_y - 3 * mm, table_w, 8 * mm, 3, stroke=1, fill=1)

    p.setFillColorRGB(*navy)
    p.setFont("Helvetica-Bold", 9.5)
    p.drawString(table_x + 5 * mm, total_y, "Total Amount:")
    p.drawRightString(table_x + table_w - 5 * mm, total_y, f"{payment.amount} BDT")

    sig_y = 22 * mm

    p.setStrokeColorRGB(*navy)
    p.setLineWidth(0.75)
    p.line(table_x + 8 * mm, sig_y, table_x + 58 * mm, sig_y)
    p.line(table_x + table_w - 58 * mm, sig_y, table_x + table_w - 8 * mm, sig_y)

    p.setFillColorRGB(*muted)
    p.setFont("Helvetica", 7)
    p.drawCentredString(table_x + 33 * mm, sig_y - 4 * mm, "Student Signature")
    p.drawCentredString(table_x + table_w - 33 * mm, sig_y - 4 * mm, "Accounts Officer Signature")

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