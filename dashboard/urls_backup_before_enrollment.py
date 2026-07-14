from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),

    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile_page, name='student_profile_page'),
    path('student/courses/', views.student_courses_page, name='student_courses_page'),
    path('student/payments/', views.student_payments_page, name='student_payments_page'),
    path('student/attendance/', views.student_attendance_page, name='student_attendance_page'),
    path('student/exam-routine/', views.student_exam_routine_page, name='student_exam_routine_page'),
    path('student/seat-plan/', views.student_seat_plan_page, name='student_seat_plan_page'),
    path('student/results/', views.student_results_page, name='student_results_page'),
    path('student/results/download/', views.download_student_result_pdf, name='download_student_result_pdf'),
    path('student/materials/', views.student_materials_page, name='student_materials_page'),
    path('student/applications/', views.student_applications_page, name='student_applications_page'),
    path('student/applications/submit/', views.submit_application, name='submit_application'),
    path('student/admit-card/', views.student_admit_card_page, name='student_admit_card_page'),
    path('student/admit-card/download/', views.download_admit_card, name='download_admit_card'),
    path('student/assignments/', views.student_assignments_page, name='student_assignments_page'),
    path('student/assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),

    # Faculty
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/reports/', views.faculty_reports, name='faculty_reports'),
    path('faculty/course/<int:offering_id>/students/', views.faculty_course_students, name='faculty_course_students'),
    path('faculty/course/<int:offering_id>/attendance/', views.take_attendance, name='take_attendance'),
    path('faculty/attendance-session/<int:session_id>/delete/', views.delete_attendance_session, name='delete_attendance_session'),
    path('faculty/course/<int:offering_id>/marks/', views.enter_marks, name='enter_marks'),
    path('faculty/course/<int:offering_id>/materials/', views.course_materials, name='course_materials'),
    path('faculty/course-material/<int:material_id>/delete/', views.delete_course_material, name='delete_course_material'),
    path('faculty/course/<int:offering_id>/assignments/', views.faculty_assignments, name='faculty_assignments'),
    path('faculty/assignment/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('faculty/assignment/<int:assignment_id>/submissions/', views.faculty_assignment_submissions, name='faculty_assignment_submissions'),
    path('faculty/course/<int:offering_id>/report/', views.faculty_course_report, name='faculty_course_report'),
    path('faculty/course/<int:offering_id>/report/download/', views.download_faculty_course_report, name='download_faculty_course_report'),
    path('faculty/applications/', views.faculty_applications, name='faculty_applications'),
    path('faculty/applications/<int:application_id>/', views.faculty_application_detail, name='faculty_application_detail'),
    path('faculty/hall-duties/', views.faculty_hall_duties, name='faculty_hall_duties'),

    # Department Head
    path('dept-head/', views.dept_head_dashboard, name='dept_head_dashboard'),
    path('academic-setup/', views.academic_setup, name='academic_setup'),

    # Exam Controller
    path('exam-controller/', views.exam_controller_dashboard, name='exam_controller_dashboard'),

    path('exam-controller/result-preview/', views.exam_result_preview, name='exam_result_preview'),
    path('exam-controller/result-preview/publish/', views.publish_result_from_preview, name='publish_result_from_preview'),
    path('exam-controller/semester-transcript/download/', views.download_semester_transcript, name='download_semester_transcript'),

    path('exam-controller/routine/<int:routine_id>/edit/', views.edit_exam_routine, name='edit_exam_routine'),
    path('exam-controller/routine/<int:routine_id>/delete/', views.delete_exam_routine, name='delete_exam_routine'),

    path('exam-controller/seat-plan/<int:seat_plan_id>/edit/', views.edit_seat_plan, name='edit_seat_plan'),
    path('exam-controller/seat-plan/<int:seat_plan_id>/delete/', views.delete_seat_plan, name='delete_seat_plan'),

    path('exam-controller/hall-duty/<int:hall_duty_id>/edit/', views.edit_hall_duty, name='edit_hall_duty'),
    path('exam-controller/hall-duty/<int:hall_duty_id>/delete/', views.delete_hall_duty, name='delete_hall_duty'),

    path('exam-controller/result-publication/<int:publication_id>/delete/', views.delete_result_publication, name='delete_result_publication'),

    # Accounts
    path('accounts/', views.accounts_dashboard, name='accounts_dashboard'),
    path('accounts/student/<int:student_id>/', views.accounts_student_detail, name='accounts_student_detail'),
    path('accounts/receipt/<int:payment_id>/', views.download_payment_receipt, name='download_payment_receipt'),

    path('accounts/fee/<int:fee_id>/delete/', views.delete_student_fee, name='delete_student_fee'),
    path('accounts/payment/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    path('accounts/waiver/<int:waiver_id>/delete/', views.delete_waiver, name='delete_waiver'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/users/', views.user_management, name='user_management'),
]