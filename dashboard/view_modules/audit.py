import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date

from dashboard.models import AuditLog


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR')


def create_audit_log(
    request,
    action,
    module,
    description='',
    target_model='',
    target_id='',
    target_repr=''
):
    try:
        actor = None

        if request.user.is_authenticated:
            actor = request.user

        AuditLog.objects.create(
            actor=actor,
            action=action,
            module=module,
            description=description,
            target_model=target_model,
            target_id=str(target_id) if target_id else '',
            target_repr=str(target_repr) if target_repr else '',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
    except Exception:
        pass


def get_filtered_audit_logs(request):
    search_query = request.GET.get('q', '')
    selected_module = request.GET.get('module', '')
    selected_action = request.GET.get('action', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    logs = AuditLog.objects.select_related(
        'actor'
    ).all()

    if search_query:
        logs = logs.filter(
            Q(actor__username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(module__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(target_model__icontains=search_query) |
            Q(target_id__icontains=search_query) |
            Q(target_repr__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )

    if selected_module:
        logs = logs.filter(module=selected_module)

    if selected_action:
        logs = logs.filter(action=selected_action)

    parsed_start_date = parse_date(start_date) if start_date else None
    parsed_end_date = parse_date(end_date) if end_date else None

    if parsed_start_date:
        logs = logs.filter(created_at__date__gte=parsed_start_date)

    if parsed_end_date:
        logs = logs.filter(created_at__date__lte=parsed_end_date)

    return logs


@login_required
def audit_logs(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')

    search_query = request.GET.get('q', '')
    selected_module = request.GET.get('module', '')
    selected_action = request.GET.get('action', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    logs = get_filtered_audit_logs(request)

    module_choices = AuditLog.objects.exclude(
        module=''
    ).values_list(
        'module',
        flat=True
    ).distinct().order_by('module')

    action_choices = AuditLog.objects.exclude(
        action=''
    ).values_list(
        'action',
        flat=True
    ).distinct().order_by('action')

    context = {
        'logs': logs[:300],
        'search_query': search_query,
        'selected_module': selected_module,
        'selected_action': selected_action,
        'start_date': start_date,
        'end_date': end_date,
        'module_choices': module_choices,
        'action_choices': action_choices,
        'total_logs': logs.count(),
    }

    return render(request, 'dashboard/audit_logs.html', context)


@login_required
def export_audit_logs(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')

    logs = get_filtered_audit_logs(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs_export.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'Time',
        'Actor Username',
        'Actor Role',
        'Module',
        'Action',
        'Target Model',
        'Target ID',
        'Target',
        'Description',
        'IP Address',
        'User Agent',
    ])

    for log in logs:
        actor_username = ''
        actor_role = ''

        if log.actor:
            actor_username = log.actor.username
            actor_role = log.actor.get_role_display()

        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            actor_username,
            actor_role,
            log.module,
            log.action,
            log.target_model,
            log.target_id,
            log.target_repr,
            log.description,
            log.ip_address,
            log.user_agent,
        ])

    return response