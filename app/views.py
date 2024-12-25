from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect
from app.models import Admin

def handle_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            admin_user = Admin.objects.get(username=username)
            if check_password(password, admin_user.password):
                request.session['admin_id'] = admin_user.id
                request.session['admin_username'] = admin_user.username
                return True
            else:
                messages.error(request, 'Invalid username or password')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    return False

def main_view(request):
    if request.session.get('admin_id'):
        return render(request, 'main.html')
    else:
        if handle_login(request):
            return redirect('main')
        return render(request, 'login.html')

def login_view(request):
    if request.session.get('admin_id'):
        return redirect('main')
    else:
        if handle_login(request):
            return redirect('main')
        return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('main')

def account_view(request):
    if not request.session.get('admin_id'):
        return redirect('main')
    columns = [field.name for field in Admin._meta.fields if field.name != 'password']
    rows = Admin.objects.all()
    context = {
        'columns': columns,
        'rows': rows,
    }
    return render(request, 'account.html', context)

def account_add_view(request):
    if request.method == 'POST':
        try:
            admin_data = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}
            admin_data['password'] = make_password(admin_data['password'])
            Admin.objects.create(**admin_data)
            messages.success(request, 'Admin added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding admin: {e}')
    return redirect('account')
