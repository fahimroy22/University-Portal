import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date

from accounts.models import User
from academics.models import Department, Batch, Semester
from students.models import StudentProfile
from finance.models import (
    ProgramFeeStructure,
    WaiverPolicy,
    FeeType,
    StudentFinancialProfile,
    StudentFee,
    Waiver,
)
from dashboard.view_modules.audit import create_audit_log


VALID_ADMISSION_CATEGORIES = ['regular', 'diploma', 'masters', 'special']


def safe_decimal(value):
    try:
        if value in [None, '']:
            return Decimal('0.00')
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def get_or_create_fee_type(name):
    fee_type, created = FeeType.objects.get_or_create(name=name)
    return fee_type


def find_regular_waiver(program_fee, combined_gpa, admission_category):
    if combined_gpa is None:
        return Decimal('0.00')

    policy = WaiverPolicy.objects.filter(
        program_fee=program_fee,
        admission_category=admission_category,
        gpa_min__lte=combined_gpa,
        gpa_max__gte=combined_gpa,
        is_active=True
    ).order_by('-gpa_min').first()

    if not policy:
        policy = WaiverPolicy.objects.filter(
            program_fee__isnull=True,
            admission_category=admission_category,
            gpa_min__lte=combined_gpa,
            gpa_max__gte=combined_gpa,
            is_active=True
        ).order_by('-gpa_min').first()

    if policy:
        return policy.waiver_amount

    return Decimal('0.00')


@login_required
def bulk_student_upload(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')

    required_columns = [
        'student_id',
        'username',
        'password',
        'first_name',
        'last_name',
        'email',
        'phone',
        'gender',
        'date_of_birth',
        'department_code',
        'batch_name',
        'current_semester_number',
        'admission_session',
        'guardian_name',
        'guardian_phone',
        'address',
        'program_name',
        'admission_category',
        'ssc_gpa',
        'hsc_gpa',
    ]

    if request.GET.get('sample') == '1':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bulk_student_upload_with_finance_sample.csv"'

        writer = csv.writer(response)
        writer.writerow(required_columns)

        writer.writerow([
            'UGV-CSE-101',
            'ugv_cse_101',
            'student123',
            'Rahim',
            'Ahmed',
            'rahim@example.com',
            '01700000001',
            'male',
            '2005-01-15',
            '001',
            '001 - Summer - 2026',
            '1',
            'Summer 2026',
            'Karim Ahmed',
            '01800000001',
            'Dhaka, Bangladesh',
            'B.Sc in CSE',
            'regular',
            '5.00',
            '5.00',
        ])

        return response

    upload_result = None
    error_rows = []

    if request.method == 'POST':
        uploaded_file = request.FILES.get('csv_file')

        if not uploaded_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('bulk_student_upload')

        if not uploaded_file.name.endswith('.csv'):
            messages.error(request, "Only CSV files are supported.")
            return redirect('bulk_student_upload')

        decoded_file = io.TextIOWrapper(
            uploaded_file.file,
            encoding='utf-8-sig'
        )

        reader = csv.DictReader(decoded_file)

        missing_columns = []

        for column in required_columns:
            if column not in reader.fieldnames:
                missing_columns.append(column)

        if missing_columns:
            messages.error(
                request,
                "Missing required columns: " + ", ".join(missing_columns)
            )
            return redirect('bulk_student_upload')

        created_count = 0
        finance_created_count = 0
        skipped_username_count = 0
        skipped_student_id_count = 0
        skipped_email_count = 0
        invalid_department_count = 0
        invalid_batch_count = 0
        invalid_semester_count = 0
        invalid_program_count = 0
        invalid_category_count = 0
        invalid_gpa_count = 0
        error_count = 0

        admission_fee_type = get_or_create_fee_type('Admission Fee')
        semester_fee_type = get_or_create_fee_type('Semester Fee')

        for row_number, row in enumerate(reader, start=2):
            student_id = row.get('student_id', '').strip()
            username = row.get('username', '').strip()
            password = row.get('password', '').strip()

            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            email = row.get('email', '').strip()
            phone = row.get('phone', '').strip()
            gender = row.get('gender', '').strip().lower() or None
            date_of_birth_raw = row.get('date_of_birth', '').strip()
            address = row.get('address', '').strip()

            raw_department_code = row.get('department_code', '').strip()

            if raw_department_code.isdigit() and len(raw_department_code) < 3:
                department_code = raw_department_code.zfill(3)
            else:
                department_code = raw_department_code

            batch_name = row.get('batch_name', '').strip()
            current_semester_number = row.get('current_semester_number', '').strip()
            
            batch_name = row.get('batch_name', '').strip()
            current_semester_number = row.get('current_semester_number', '').strip()

            admission_session = row.get('admission_session', '').strip()
            guardian_name = row.get('guardian_name', '').strip()
            guardian_phone = row.get('guardian_phone', '').strip()

            program_name = row.get('program_name', '').strip()
            admission_category = row.get('admission_category', '').strip().lower() or 'regular'
            ssc_gpa = safe_decimal(row.get('ssc_gpa', '').strip())
            hsc_gpa = safe_decimal(row.get('hsc_gpa', '').strip())

            if not student_id or not username or not password:
                error_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'student_id, username, and password are required.'
                })
                continue

            if admission_category not in VALID_ADMISSION_CATEGORIES:
                invalid_category_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'Invalid admission_category. Use regular, diploma, masters, or special.'
                })
                continue

            if not program_name:
                invalid_program_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'program_name is required for finance setup.'
                })
                continue

            if ssc_gpa is None or hsc_gpa is None:
                invalid_gpa_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'Invalid SSC or HSC GPA. Use numbers like 5.00.'
                })
                continue

            if ssc_gpa < 0 or ssc_gpa > 5 or hsc_gpa < 0 or hsc_gpa > 5:
                invalid_gpa_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'SSC GPA and HSC GPA must be between 0.00 and 5.00.'
                })
                continue

            if User.objects.filter(username=username).exists():
                skipped_username_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Username already exists: {username}'
                })
                continue

            if StudentProfile.objects.filter(student_id=student_id).exists():
                skipped_student_id_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Student ID already exists: {student_id}'
                })
                continue

            if email and User.objects.filter(email=email).exists():
                skipped_email_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Email already exists: {email}'
                })
                continue

            department = Department.objects.filter(
                code=department_code
            ).first()

            if not department:
                invalid_department_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Department not found with code: {department_code}'
                })
                continue

            batch = Batch.objects.filter(
                department=department,
                batch_name=batch_name
            ).first()

            if not batch:
                invalid_batch_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Batch not found: {batch_name} under department {department_code}'
                })
                continue

            semester = Semester.objects.filter(
                number=current_semester_number
            ).first()

            if not semester:
                invalid_semester_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Semester not found with number: {current_semester_number}'
                })
                continue

            program_fee = ProgramFeeStructure.objects.filter(
                program_name__iexact=program_name,
                department=department,
                is_active=True
            ).first()

            if not program_fee:
                program_fee = ProgramFeeStructure.objects.filter(
                    program_name__iexact=program_name,
                    department__isnull=True,
                    is_active=True
                ).first()

            if not program_fee:
                invalid_program_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Program fee structure not found: {program_name} under department {department_code}'
                })
                continue

            date_of_birth = None

            if date_of_birth_raw:
                date_of_birth = parse_date(date_of_birth_raw)

                if not date_of_birth:
                    error_count += 1
                    error_rows.append({
                        'row_number': row_number,
                        'reason': 'Invalid date format. Use YYYY-MM-DD.'
                    })
                    continue

            if gender and gender not in ['male', 'female', 'other']:
                error_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': 'Invalid gender. Use male, female, or other.'
                })
                continue

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        role='student',
                        phone=phone,
                        gender=gender,
                        date_of_birth=date_of_birth,
                        address=address,
                        is_active=True,
                    )

                    student = StudentProfile.objects.create(
                        user=user,
                        student_id=student_id,
                        department=department,
                        batch=batch,
                        current_semester=semester,
                        admission_session=admission_session,
                        guardian_name=guardian_name,
                        guardian_phone=guardian_phone,
                        address=address,
                        is_active=True,
                    )

                    combined_gpa = ssc_gpa + hsc_gpa
                    regular_waiver_amount = find_regular_waiver(
                        program_fee,
                        combined_gpa,
                        admission_category
                    )

                    financial_profile = StudentFinancialProfile.objects.create(
                        student=student,
                        program_fee=program_fee,
                        admission_category=admission_category,
                        ssc_gpa=ssc_gpa,
                        hsc_gpa=hsc_gpa,
                        combined_gpa=combined_gpa,
                        admission_fee=program_fee.admission_fee,
                        semester_fee_before_waiver=program_fee.semester_fee,
                        regular_waiver_amount=regular_waiver_amount,
                        special_waiver_amount=Decimal('0.00'),
                        total_semesters=program_fee.total_semesters,
                        created_by=request.user,
                        updated_by=request.user,
                    )

                    StudentFee.objects.create(
                        student=student,
                        fee_type=admission_fee_type,
                        semester=None,
                        original_amount=financial_profile.admission_fee,
                        waiver_amount=Decimal('0.00'),
                        amount=financial_profile.admission_fee,
                        paid_amount=Decimal('0.00'),
                        is_paid=False,
                        status='unpaid',
                        note='Admission fee generated during bulk student upload.'
                    )

                    semester_fee = StudentFee.objects.create(
                        student=student,
                        fee_type=semester_fee_type,
                        semester=semester,
                        original_amount=financial_profile.semester_fee_before_waiver,
                        waiver_amount=financial_profile.regular_waiver_amount,
                        amount=financial_profile.final_semester_fee,
                        paid_amount=Decimal('0.00'),
                        is_paid=False,
                        status='unpaid',
                        note='Current semester fee generated during bulk student upload.'
                    )

                    if financial_profile.regular_waiver_amount > 0:
                        waiver_source = 'gpa'

                        if admission_category in ['diploma', 'masters', 'special']:
                            waiver_source = 'manual'

                        Waiver.objects.create(
                            student=student,
                            student_fee=semester_fee,
                            amount=financial_profile.regular_waiver_amount,
                            source=waiver_source,
                            reason=(
                                f'Automatic waiver applied. '
                                f'Category: {admission_category}. '
                                f'SSC GPA: {ssc_gpa}, HSC GPA: {hsc_gpa}, '
                                f'Combined GPA: {combined_gpa}.'
                            ),
                            approved_by='System'
                        )

                    created_count += 1
                    finance_created_count += 1

            except Exception as exc:
                error_count += 1
                error_rows.append({
                    'row_number': row_number,
                    'reason': f'Unexpected error while creating student: {exc}'
                })
                continue

        upload_result = {
            'created_count': created_count,
            'finance_created_count': finance_created_count,
            'skipped_username_count': skipped_username_count,
            'skipped_student_id_count': skipped_student_id_count,
            'skipped_email_count': skipped_email_count,
            'invalid_department_count': invalid_department_count,
            'invalid_batch_count': invalid_batch_count,
            'invalid_semester_count': invalid_semester_count,
            'invalid_program_count': invalid_program_count,
            'invalid_category_count': invalid_category_count,
            'invalid_gpa_count': invalid_gpa_count,
            'error_count': error_count,
            'total_problem_rows': len(error_rows),
        }

        create_audit_log(
            request,
            action='BULK_UPLOAD',
            module='Bulk Student Upload',
            description=(
                f'Bulk student upload completed with finance setup. '
                f'Created: {created_count}, '
                f'Finance profiles: {finance_created_count}, '
                f'Duplicate usernames: {skipped_username_count}, '
                f'Duplicate student IDs: {skipped_student_id_count}, '
                f'Duplicate emails: {skipped_email_count}, '
                f'Invalid departments: {invalid_department_count}, '
                f'Invalid batches: {invalid_batch_count}, '
                f'Invalid semesters: {invalid_semester_count}, '
                f'Invalid programs: {invalid_program_count}, '
                f'Invalid categories: {invalid_category_count}, '
                f'Invalid GPA rows: {invalid_gpa_count}, '
                f'Other errors: {error_count}, '
                f'Total skipped/problem rows: {len(error_rows)}.'
            ),
            target_model='StudentProfile',
            target_id='bulk',
            target_repr='Bulk student CSV upload with finance setup',
        )

        if created_count > 0:
            messages.success(
                request,
                f"{created_count} student account(s) created successfully with finance setup."
            )

        if error_rows:
            messages.warning(
                request,
                f"{len(error_rows)} row(s) were skipped. Check details below."
            )

        if created_count == 0 and not error_rows:
            messages.info(request, "No student account was created.")

    context = {
        'required_columns': required_columns,
        'upload_result': upload_result,
        'error_rows': error_rows,
    }

    return render(request, 'dashboard/bulk_student_upload.html', context)