from django.urls import path
from . import views

app_name = 'attendance_module'

urlpatterns = [
    path('mark/', views.mark_attendance, name='mark'),
    path('manage/', views.manage_attendance, name='manage'),
    path('add/', views.add_attendance_record, name='add'),
    path('edit/<int:attendance_id>/', views.edit_attendance_record, name='edit'),
]
