from django.urls import path
from . import views

app_name = 'reports_module'

urlpatterns = [
    path('employee/', views.employee_report, name='employee'),
    path('attendance/', views.attendance_report, name='attendance'),
    path('leave/', views.leave_report, name='leave'),
]
