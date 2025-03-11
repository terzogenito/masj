from django.urls import path
from . import views
from django.shortcuts import render
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.main_view, name='main'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('account/', views.account_view, name='account'),
    path('account-add/', views.account_add_view, name='account_add'),
    path('data/', views.data_view, name='data_view'),
    path('data-export/', views.export_all, name='export_all'),
    path('table-add/', views.table_add, name='table_add'),
    path('table-import/', views.table_import, name='table_import'),
    path('table-export/<str:table_name>/', views.table_export, name='table_export'),
    path('table-drop/', views.table_drop, name='table_drop'),
    path('table/<str:table_name>/', views.table, name='table'),
    path('table-row/<str:table_name>/', views.table_row, name='table_row'),
    path('field/<str:table_name>/', views.field_view, name='field'),
    path('field-add/<str:table_name>/', views.field_add, name='field_add'),
]

def custom_403_view(request, exception):
    return render(request, '403.html', status=403)
handler403 = 'app.urls.custom_403_view'

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)
handler404 = 'app.urls.custom_404_view'

def custom_500_view(request):
    return render(request, '500.html', status=500)
handler500 = 'app.urls.custom_500_view'