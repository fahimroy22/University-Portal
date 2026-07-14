from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            'UGV Profile Information',
            {
                'fields': (
                    'role',
                    'employee_id',
                    'staff_department',
                    'designation',
                    'office_room',
                    'phone',
                    'gender',
                    'date_of_birth',
                    'address',
                    'profile_photo',
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'UGV Profile Information',
            {
                'fields': (
                    'role',
                    'employee_id',
                    'staff_department',
                    'designation',
                    'office_room',
                    'phone',
                    'gender',
                    'date_of_birth',
                    'address',
                    'profile_photo',
                )
            }
        ),
    )

    list_display = (
        'username',
        'employee_id',
        'email',
        'first_name',
        'last_name',
        'role',
        'staff_department',
        'designation',
        'phone',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'staff_department',
        'gender',
        'is_staff',
        'is_active',
        'is_superuser',
    )

    search_fields = (
        'username',
        'employee_id',
        'email',
        'first_name',
        'last_name',
        'phone',
        'staff_department__code',
        'staff_department__name',
    )


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomUserAdmin)