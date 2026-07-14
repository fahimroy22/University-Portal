from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def my_profile(request):
    user = request.user

    if request.method == 'POST':
        messages.error(
            request,
            "You cannot edit your own profile. Please contact Admin or Super Admin for profile updates."
        )
        return redirect('my_profile')

    context = {
        'profile_user': user,
        'can_edit_own_profile': False,
    }

    return render(request, 'dashboard/my_profile.html', context)