from dashboard.view_modules.common import dashboard_redirect

from dashboard.view_modules.student import (
    calculate_student_dashboard_data,
    student_dashboard,
    submit_application,
    download_admit_card,
    student_profile_page,
    student_courses_page,
    student_course_summary_page,
    student_payments_page,
    student_attendance_page,
    student_exam_routine_page,
    student_seat_plan_page,
    student_results_page,
    download_student_result_pdf,
    student_materials_page,
    student_applications_page,
    student_admit_card_page,
    student_assignments_page,
    submit_assignment,
    download_student_payment_receipt,
    student_mark_review_requests,
    student_create_mark_review_request,
)

from dashboard.view_modules.faculty import (
    faculty_dashboard,
    faculty_course_action_page,
    faculty_course_students,
    take_attendance,
    delete_attendance_session,
    enter_marks,
    course_materials,
    delete_course_material,
    faculty_assignments,
    edit_assignment,
    faculty_assignment_submissions,
    faculty_reports,
    faculty_course_report,
    download_faculty_course_report,
    faculty_applications,
    faculty_application_detail,
    faculty_hall_duties,

    # Mark correction workflow
    faculty_mark_review_requests,
    faculty_mark_review_request_detail,
    faculty_correction_requests,
    faculty_create_correction_request,
    faculty_correction_request_detail,
)

from dashboard.view_modules.accounts import (
    accounts_dashboard,
    accounts_students,
    accounts_payments,
    accounts_dues,
    accounts_waivers,
    accounts_receipts,
    accounts_admit_cards,
    accounts_reports,
    accounts_student_detail,
    delete_student_fee,
    delete_payment,
    delete_waiver,
    download_payment_receipt,
    download_accounts_admit_card,
)

from dashboard.view_modules.exam_controller import (
    exam_controller_dashboard,

    exam_create_routine,
    exam_create_seat_plan,
    exam_assign_hall_duty,
    exam_publish_result,

    exam_manage_student_results,
    exam_student_result_detail,
    exam_result_correction_request,

    result_correction_requests,
    review_result_correction_request,

    exam_result_preview,
    publish_result_from_preview,
    download_semester_transcript,

    edit_exam_routine,
    delete_exam_routine,

    edit_seat_plan,
    delete_seat_plan,

    edit_hall_duty,
    delete_hall_duty,

    delete_result_publication,
    exam_semester_result_review,
    publish_semester_results,
    download_semester_transcript_by_student,
    exam_correction_requests,
    exam_correction_request_detail,
)

from dashboard.view_modules.academic import (
    academic_setup,
    dept_head_dashboard,
    admin_dashboard,
    super_admin_dashboard,
)

from dashboard.view_modules.user_management import (
    user_management,
    create_user,
    user_detail,
)
from dashboard.view_modules.enrollment import course_enrollment
from dashboard.view_modules.bulk_student_upload import bulk_student_upload

from dashboard.view_modules.notices import (
    notice_management,
    my_notices,
)

from dashboard.view_modules.audit import (
    audit_logs,
    export_audit_logs,
)

from dashboard.view_modules.system_settings import system_settings
from dashboard.view_modules.profile import my_profile