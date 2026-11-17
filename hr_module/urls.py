from django.urls import path
from . import views

app_name = 'hr_module'

urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='dashboard'),
    path('employees/', views.manage_employees, name='manage_employees'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
]
