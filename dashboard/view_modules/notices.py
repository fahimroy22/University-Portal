import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render

from academics.models import Batch, CourseOffering, Department
from dashboard.view_modules.audit import create_audit_log
from notices.models import Notice
from students.models import StudentProfile


NOTICE_MANAGEMENT_ROLES = [
    'super_admin',
    'admin',
    'dept_head',
    'exam_controller',
    'accounts',
]


def get_notice_reference(notice):
    """
    Convert the database primary key into a readable notice reference.

    Example:
        1 -> NTC-000001
    """
    return f'NTC-{notice.pk:06d}'


def extract_notice_id(search_text):
    """
    Accept searches such as:

    NTC-000001
    NTC000001
    NTC 000001
    000001
    1
    """
    if not search_text:
        return None

    normalized = search_text.strip().upper()

    match = re.fullmatch(
        r'(?:NTC[\s-]?)?0*(\d+)',
        normalized,
    )

    if not match:
        return None

    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def add_notice_references(notices):
    """
    Add a temporary reference_id property for template display.
    """
    for notice in notices:
        notice.reference_id = get_notice_reference(notice)

    return notices


def validate_notice_target(target_audience, department, batch):
    if target_audience == 'department' and not department:
        return 'Please select a department for the department notice.'

    if target_audience == 'batch' and not batch:
        return 'Please select a batch for the batch notice.'

    return None


def get_selected_department(department_id):
    if not department_id:
        return None

    return Department.objects.filter(
        id=department_id
    ).first()


def get_selected_batch(batch_id):
    if not batch_id:
        return None

    return Batch.objects.select_related(
        'department'
    ).filter(
        id=batch_id
    ).first()


def get_notices_for_user(user):
    notices = Notice.objects.filter(
        is_published=True
    ).select_related(
        'department',
        'batch',
        'published_by',
    ).order_by(
        '-published_at',
        '-id',
    )

    if user.role == 'super_admin':
        return notices

    if user.role == 'admin':
        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='admin')
        )

    if user.role == 'exam_controller':
        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='exam_controller')
        )

    if user.role == 'accounts':
        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='accounts')
        )

    if user.role == 'student':
        profile = StudentProfile.objects.filter(
            user=user
        ).select_related(
            'department',
            'batch',
        ).first()

        if not profile:
            return Notice.objects.none()

        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='students')
            | Q(
                target_audience='department',
                department=profile.department,
            )
            | Q(
                target_audience='batch',
                batch=profile.batch,
            )
        )

    if user.role == 'faculty':
        department_ids = CourseOffering.objects.filter(
            faculty=user
        ).values_list(
            'course__department_id',
            flat=True,
        ).distinct()

        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='faculty')
            | Q(
                target_audience='department',
                department_id__in=department_ids,
            )
        )

    if user.role == 'dept_head':
        return notices.filter(
            Q(target_audience='all')
            | Q(target_audience='department')
        )

    return Notice.objects.none()


@login_required
def notice_management(request):
    if request.user.role not in NOTICE_MANAGEMENT_ROLES:
        return redirect('dashboard')

    departments = Department.objects.all().order_by('code')

    batches = Batch.objects.select_related(
        'department'
    ).order_by(
        'department__code',
        'admission_year',
        'batch_name',
    )

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'create_notice':
            title = request.POST.get('title', '').strip()
            message_text = request.POST.get('message', '').strip()
            notice_type = request.POST.get('notice_type') or 'general'
            target_audience = request.POST.get('target_audience') or 'all'
            department = get_selected_department(
                request.POST.get('department')
            )
            batch = get_selected_batch(
                request.POST.get('batch')
            )
            attachment = request.FILES.get('attachment')
            is_published = request.POST.get('is_published') == 'on'

            if not title or not message_text:
                messages.error(
                    request,
                    'Please enter the notice title and message.',
                )
                return redirect('notice_management')

            validation_error = validate_notice_target(
                target_audience,
                department,
                batch,
            )

            if validation_error:
                messages.error(request, validation_error)
                return redirect('notice_management')

            notice = Notice.objects.create(
                title=title,
                message=message_text,
                notice_type=notice_type,
                target_audience=target_audience,
                department=department,
                batch=batch,
                attachment=attachment,
                is_published=is_published,
                published_by=request.user,
            )

            reference_id = get_notice_reference(notice)

            create_audit_log(
                request,
                action='CREATE',
                module='Notice Management',
                description=(
                    f'Created notice {reference_id}: {notice.title}'
                ),
                target_model='Notice',
                target_id=notice.id,
                target_repr=f'{reference_id} - {notice.title}',
            )

            messages.success(
                request,
                f'Notice created successfully. Notice ID: {reference_id}',
            )

            return redirect('notice_management')

        if action == 'update_notice':
            notice_id = request.POST.get('notice_id')

            notice = Notice.objects.filter(
                id=notice_id
            ).first()

            if not notice:
                messages.error(request, 'Notice not found.')
                return redirect('notice_management')

            title = request.POST.get('title', '').strip()
            message_text = request.POST.get('message', '').strip()
            notice_type = request.POST.get('notice_type') or 'general'
            target_audience = request.POST.get('target_audience') or 'all'
            department = get_selected_department(
                request.POST.get('department')
            )
            batch = get_selected_batch(
                request.POST.get('batch')
            )
            attachment = request.FILES.get('attachment')
            is_published = request.POST.get('is_published') == 'on'

            if not title or not message_text:
                messages.error(
                    request,
                    'Please enter the notice title and message.',
                )
                return redirect(
                    f'{request.path}?edit={notice.id}'
                )

            validation_error = validate_notice_target(
                target_audience,
                department,
                batch,
            )

            if validation_error:
                messages.error(request, validation_error)
                return redirect(
                    f'{request.path}?edit={notice.id}'
                )

            notice.title = title
            notice.message = message_text
            notice.notice_type = notice_type
            notice.target_audience = target_audience
            notice.department = department
            notice.batch = batch
            notice.is_published = is_published

            if attachment:
                notice.attachment = attachment

            notice.save()

            reference_id = get_notice_reference(notice)

            create_audit_log(
                request,
                action='UPDATE',
                module='Notice Management',
                description=(
                    f'Updated notice {reference_id}: {notice.title}'
                ),
                target_model='Notice',
                target_id=notice.id,
                target_repr=f'{reference_id} - {notice.title}',
            )

            messages.success(
                request,
                f'{reference_id} updated successfully.',
            )

            return redirect('notice_management')

        if action == 'toggle_notice':
            notice_id = request.POST.get('notice_id')

            notice = Notice.objects.filter(
                id=notice_id
            ).first()

            if not notice:
                messages.error(request, 'Notice not found.')
                return redirect('notice_management')

            notice.is_published = not notice.is_published
            notice.save(update_fields=['is_published'])

            reference_id = get_notice_reference(notice)

            create_audit_log(
                request,
                action=(
                    'PUBLISH'
                    if notice.is_published
                    else 'UNPUBLISH'
                ),
                module='Notice Management',
                description=(
                    f'Changed status for {reference_id}: {notice.title}'
                ),
                target_model='Notice',
                target_id=notice.id,
                target_repr=f'{reference_id} - {notice.title}',
            )

            if notice.is_published:
                messages.success(
                    request,
                    f'{reference_id} published successfully.',
                )
            else:
                messages.warning(
                    request,
                    f'{reference_id} moved to drafts.',
                )

            return redirect('notice_management')

        if action == 'delete_notice':
            notice_id = request.POST.get('notice_id')

            notice = Notice.objects.filter(
                id=notice_id
            ).first()

            if not notice:
                messages.error(request, 'Notice not found.')
                return redirect('notice_management')

            reference_id = get_notice_reference(notice)
            notice_title = notice.title
            saved_notice_id = notice.id

            create_audit_log(
                request,
                action='DELETE',
                module='Notice Management',
                description=(
                    f'Deleted notice {reference_id}: {notice_title}'
                ),
                target_model='Notice',
                target_id=saved_notice_id,
                target_repr=f'{reference_id} - {notice_title}',
            )

            notice.delete()

            messages.success(
                request,
                f'{reference_id} deleted successfully.',
            )

            return redirect('notice_management')

    notices = Notice.objects.select_related(
        'department',
        'batch',
        'published_by',
    ).order_by(
        '-published_at',
        '-id',
    )

    query = request.GET.get('q', '').strip()
    selected_notice_type = request.GET.get('notice_type', '').strip()
    selected_audience = request.GET.get('target_audience', '').strip()
    selected_department = request.GET.get('department', '').strip()
    selected_status = request.GET.get('status', '').strip()

    if query:
        notice_database_id = extract_notice_id(query)

        search_filter = (
            Q(title__icontains=query)
            | Q(message__icontains=query)
            | Q(published_by__username__icontains=query)
        )

        if notice_database_id is not None:
            search_filter |= Q(id=notice_database_id)

        notices = notices.filter(search_filter)

    if selected_notice_type:
        notices = notices.filter(
            notice_type=selected_notice_type
        )

    if selected_audience:
        notices = notices.filter(
            target_audience=selected_audience
        )

    if selected_department:
        notices = notices.filter(
            department_id=selected_department
        )

    if selected_status == 'published':
        notices = notices.filter(is_published=True)
    elif selected_status == 'draft':
        notices = notices.filter(is_published=False)

    all_notice_count = Notice.objects.count()
    published_notice_count = Notice.objects.filter(
        is_published=True
    ).count()
    draft_notice_count = Notice.objects.filter(
        is_published=False
    ).count()
    attachment_notice_count = Notice.objects.exclude(
        attachment=''
    ).exclude(
        attachment__isnull=True
    ).count()

    paginator = Paginator(notices, 15)
    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    add_notice_references(page_obj.object_list)

    edit_notice = None
    edit_notice_id = request.GET.get('edit')

    if edit_notice_id:
        edit_notice = Notice.objects.select_related(
            'department',
            'batch',
            'published_by',
        ).filter(
            id=edit_notice_id
        ).first()

        if edit_notice:
            edit_notice.reference_id = get_notice_reference(
                edit_notice
            )

    context = {
        'notices': page_obj.object_list,
        'page_obj': page_obj,
        'edit_notice': edit_notice,
        'departments': departments,
        'batches': batches,
        'notice_type_choices': Notice.NOTICE_TYPE_CHOICES,
        'target_audience_choices': Notice.TARGET_AUDIENCE_CHOICES,
        'query': query,
        'selected_notice_type': selected_notice_type,
        'selected_audience': selected_audience,
        'selected_department': selected_department,
        'selected_status': selected_status,
        'all_notice_count': all_notice_count,
        'published_notice_count': published_notice_count,
        'draft_notice_count': draft_notice_count,
        'attachment_notice_count': attachment_notice_count,
    }

    return render(
        request,
        'dashboard/notice_management.html',
        context,
    )


@login_required
def my_notices(request):
    notices = get_notices_for_user(request.user)

    add_notice_references(notices)

    context = {
        'notices': notices,
    }

    return render(
        request,
        'dashboard/my_notices.html',
        context,
    )