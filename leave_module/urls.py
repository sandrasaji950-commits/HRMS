from django.urls import path
from . import views

app_name = 'leave_module'

urlpatterns = [
    path('apply/', views.apply_leave, name='apply'),
    path('history/', views.leave_history, name='history'),
    path('manage/', views.manage_leaves, name='manage'),
    path('action/<int:leave_id>/<str:action_type>/', views.leave_action, name='action'),
]
