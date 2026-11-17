from django.urls import path
from . import views

app_name = 'employee_module'

urlpatterns = [
    path('dashboard/', views.employee_dashboard, name='dashboard'),
    path('profile/', views.employee_profile, name='profile'),
]
