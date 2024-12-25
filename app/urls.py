from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.main_view, name='main'),
]

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

handler404 = 'masj.urls.custom_404_view'