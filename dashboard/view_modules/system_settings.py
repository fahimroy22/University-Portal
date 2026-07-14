from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from dashboard.models import SystemSettings
from dashboard.view_modules.audit import create_audit_log


@login_required
def system_settings(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')

    settings_obj = SystemSettings.objects.first()

    if not settings_obj:
        settings_obj = SystemSettings.objects.create(
            updated_by=request.user
        )

    if request.method == 'POST':
        old_university_name = settings_obj.university_name
        old_short_name = settings_obj.short_name

        settings_obj.university_name = request.POST.get('university_name')
        settings_obj.short_name = request.POST.get('short_name')
        settings_obj.address = request.POST.get('address')
        settings_obj.contact_email = request.POST.get('contact_email')
        settings_obj.phone = request.POST.get('phone')
        settings_obj.website = request.POST.get('website')
        settings_obj.current_academic_session = request.POST.get('current_academic_session')
        settings_obj.result_publication_note = request.POST.get('result_publication_note')
        settings_obj.admit_card_note = request.POST.get('admit_card_note')
        settings_obj.payment_instruction = request.POST.get('payment_instruction')
        settings_obj.updated_by = request.user

        logo = request.FILES.get('logo')

        if logo:
            settings_obj.logo = logo

        if not settings_obj.university_name or not settings_obj.short_name:
            messages.error(request, "University name and short name are required.")
            return redirect('system_settings')

        settings_obj.save()

        create_audit_log(
            request,
            action='UPDATE',
            module='System Settings',
            description=(
                f'Updated system settings from '
                f'{old_short_name} - {old_university_name} '
                f'to {settings_obj.short_name} - {settings_obj.university_name}.'
            ),
            target_model='SystemSettings',
            target_id=settings_obj.id,
            target_repr=f'{settings_obj.short_name} - {settings_obj.university_name}',
        )

        messages.success(request, "System settings updated successfully.")
        return redirect('system_settings')

    context = {
        'settings_obj': settings_obj,
    }

    return render(request, 'dashboard/system_settings.html', context)