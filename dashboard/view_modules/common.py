from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


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