from dashboard.models import SystemSettings


def system_settings_context(request):
    try:
        settings_obj = SystemSettings.objects.first()
    except Exception:
        settings_obj = None

    return {
        'system_settings': settings_obj
    }