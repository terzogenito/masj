from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from app.models import Admin

def main_view(request):
    if not request.session.get('admin_id'):
        return render(request, 'login.html')
    return render(request, 'main.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin_user = Admin.objects.get(username=username)
            if check_password(password, admin_user.password):
                request.session['admin_id'] = admin_user.id
                request.session['admin_username'] = admin_user.username
                return redirect('main')
            else:
                messages.error(request, 'Invalid username or password')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('login')
