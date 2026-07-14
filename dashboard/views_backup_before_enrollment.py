from dashboard.view_modules.common import dashboard_redirect

from dashboard.view_modules.student import (
    calculate_student_dashboard_data,
    student_dashboard,
    submit_application,
    download_admit_card,
    student_profile_page,
    student_courses_page,
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
)

from dashboard.view_modules.faculty import (
    faculty_dashboard,
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
)

from dashboard.view_modules.accounts import (
    accounts_dashboard,
    accounts_student_detail,
    delete_student_fee,
    delete_payment,
    delete_waiver,
    download_payment_receipt,
)

from dashboard.view_modules.exam_controller import (
    exam_controller_dashboard,
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
)

from dashboard.view_modules.academic import (
    academic_setup,
    dept_head_dashboard,
    admin_dashboard,
    super_admin_dashboard,
)
from dashboard.view_modules.user_management import user_management