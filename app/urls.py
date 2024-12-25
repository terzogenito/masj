from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.main_view, name='main'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_view, name='account'),
]

def custom_403_view(request, exception):
    return render(request, '403.html', status=403)
handler403 = 'masj.urls.custom_403_view'

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)
handler404 = 'masj.urls.custom_404_view'

def custom_500_view(request, exception):
    return render(request, '500.html', status=500)
handler500 = 'masj.urls.custom_500_view'