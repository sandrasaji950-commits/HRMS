from django.urls import path
from . import views

app_name = 'admin_module'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('hr/', views.manage_hr, name='manage_hr'),
    path('hr/add/', views.add_hr, name='add_hr'),
    path('hr/edit/<int:user_id>/', views.edit_hr, name='edit_hr'),
    path('hr/delete/<int:user_id>/', views.delete_hr, name='delete_hr'),
]
