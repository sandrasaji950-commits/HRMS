from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib import messages

class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # 1. Allow access to static files and login/logout without authentication
        exempt_prefixes = ['/static/', '/media/']
        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return self.get_response(request)

        # Resolve the URL to see if it's the login view
        try:
            resolver_match = resolve(path)
            view_name = resolver_match.view_name
        except Resolver404:
            view_name = ''

        # Allow accounts:login without auth
        if view_name == 'accounts:login':
            # If user is already logged in, redirect to their respective dashboard
            if 'user_id' in request.session:
                role = request.session.get('role')
                if role == 'Admin':
                    return redirect('admin_module:dashboard')
                elif role == 'HR':
                    return redirect('hr_module:dashboard')
                else:
                    return redirect('employee_module:dashboard')
            return self.get_response(request)

        # 2. Check if user is authenticated (using session)
        if 'user_id' not in request.session:
            # For password reset or other specific pages if needed
            return redirect('accounts:login')

        # Attach helper attributes to request for views
        request.user_id = request.session['user_id']
        request.username = request.session['username']
        request.role = request.session['role']

        # 3. Enforce Role-Based Access Control (RBAC) on path prefixes
        role = request.role

        # Admin paths
        if path.startswith('/admin/') and role != 'Admin':
            messages.error(request, "Access Denied: Admin permissions required.")
            return self.redirect_to_dashboard(role)

        # HR paths (HR and Admin can access)
        if path.startswith('/hr/') and role not in ('HR', 'Admin'):
            messages.error(request, "Access Denied: HR Manager permissions required.")
            return self.redirect_to_dashboard(role)

        # Department management (Admin only)
        if path.startswith('/department/') and role != 'Admin':
            messages.error(request, "Access Denied: Admin permissions required to manage departments.")
            return self.redirect_to_dashboard(role)

        # Reports paths (HR and Admin only)
        if path.startswith('/reports/') and role not in ('HR', 'Admin'):
            messages.error(request, "Access Denied: HR or Admin permissions required to view reports.")
            return self.redirect_to_dashboard(role)

        # Employee paths (Employee, HR, and Admin can access, but Employee can only view their own)
        if path.startswith('/employee/') and role not in ('Employee', 'HR', 'Admin'):
            messages.error(request, "Access Denied: Invalid role access.")
            return self.redirect_to_dashboard(role)

        response = self.get_response(request)
        return response

    def redirect_to_dashboard(self, role):
        if role == 'Admin':
            return redirect('admin_module:dashboard')
        elif role == 'HR':
            return redirect('hr_module:dashboard')
        else:
            return redirect('employee_module:dashboard')
