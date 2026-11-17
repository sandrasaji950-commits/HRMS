from django.urls import path
from . import views

app_name = 'department_module'

urlpatterns = [
    path('', views.department_list, name='list'),
    path('add/', views.add_department, name='add'),
    path('edit/<int:department_id>/', views.edit_department, name='edit'),
    path('delete/<int:department_id>/', views.delete_department, name='delete'),
]
