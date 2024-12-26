from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path('', views.main_view, name='main'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_view, name='account'),
    path('account-add/', views.account_add_view, name='account_add'),
    path('data/', views.data_view, name='data_view'),
    path('table-add/', views.table_add, name='table_add'),
    path('table-drop/', views.table_drop, name='table_drop'),
    path('table/<str:table_name>/', views.table, name='table'),
    path('table/<str:table_name>/add-column/', views.add_column, name='add_column'),
    path('table-import/', views.table_import, name='table_import'),
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