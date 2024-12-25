from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages

def main_view(request):
    if request.user.is_authenticated:
        users = User.objects.select_related('profile').all()
        return render(request, 'main.html', {'users': users})
    else:
        return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')