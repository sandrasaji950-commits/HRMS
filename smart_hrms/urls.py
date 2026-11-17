"""
URL configuration for smart_hrms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('accounts:login')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('accounts/', include('accounts.urls')),
    path('admin/', include('admin_module.urls')),
    path('hr/', include('hr_module.urls')),
    path('employee/', include('employee_module.urls')),
    path('department/', include('department_module.urls')),
    path('attendance/', include('attendance_module.urls')),
    path('leave/', include('leave_module.urls')),
    path('reports/', include('reports_module.urls')),
]

