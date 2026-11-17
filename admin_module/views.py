from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from smart_hrms.db import execute_read, execute_write

def admin_dashboard(request):
    """Render admin dashboard with stats gathered via raw SQL."""
    emp_count = execute_read("SELECT COUNT(*) as count FROM employees WHERE status = 'Active'")[0]['count']
    hr_count = execute_read("SELECT COUNT(*) as count FROM users WHERE role = 'HR'")[0]['count']
    dept_count = execute_read("SELECT COUNT(*) as count FROM departments")[0]['count']
    pending_leaves = execute_read("SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'")[0]['count']

    return render(request, 'admin/dashboard.html', {
        'total_employees': emp_count,
        'total_hr': hr_count,
        'total_departments': dept_count,
        'pending_leaves': pending_leaves
    })

def manage_hr(request):
    """List all HR users."""
    hr_list = execute_read("SELECT * FROM users WHERE role = 'HR' ORDER BY id DESC")
    return render(request, 'admin/manage_hr.html', {'hr_list': hr_list})

def add_hr(request):
    """Create a new HR user."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Username and Password are required.")
            return render(request, 'admin/add_hr.html')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'admin/add_hr.html', {'username': username})

        # Check if username exists
        existing = execute_read("SELECT * FROM users WHERE username = ?", [username])
        if existing:
            messages.error(request, f"Username '{username}' already exists.")
            return render(request, 'admin/add_hr.html')

        password_hash = make_password(password)
        # Store both hash and plain password (plain_password stored as requested by user feedback)
        # TODO(security): Storing plain passwords for Admin visibility. Remove plain_password in prod.
        execute_write(
            "INSERT INTO users (username, password_hash, plain_password, role) VALUES (?, ?, ?, ?)",
            [username, password_hash, password, 'HR']
        )
        messages.success(request, f"HR Manager '{username}' created successfully.")
        return redirect('admin_module:manage_hr')

    return render(request, 'admin/add_hr.html')

def edit_hr(request, user_id):
    """Edit an HR user (update username and optionally password)."""
    users = execute_read("SELECT * FROM users WHERE id = ? AND role = 'HR'", [user_id])
    if not users:
        messages.error(request, "HR Manager not found.")
        return redirect('admin_module:manage_hr')
    hr_user = users[0]

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username:
            messages.error(request, "Username is required.")
            return render(request, 'admin/edit_hr.html', {'hr_user': hr_user})

        # Check username uniqueness (excluding current user)
        existing = execute_read("SELECT * FROM users WHERE username = ? AND id != ?", [username, user_id])
        if existing:
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'admin/edit_hr.html', {'hr_user': hr_user})

        if password:
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'admin/edit_hr.html', {'hr_user': hr_user})
            
            password_hash = make_password(password)
            # Update username and password
            # TODO(security): Storing plain passwords for Admin visibility. Remove plain_password in prod.
            execute_write(
                "UPDATE users SET username = ?, password_hash = ?, plain_password = ? WHERE id = ?",
                [username, password_hash, password, user_id]
            )
        else:
            # Update username only
            execute_write("UPDATE users SET username = ? WHERE id = ?", [username, user_id])

        messages.success(request, f"HR Manager '{username}' updated successfully.")
        return redirect('admin_module:manage_hr')

    return render(request, 'admin/edit_hr.html', {'hr_user': hr_user})

def delete_hr(request, user_id):
    """Delete an HR user."""
    if request.method == 'POST':
        # Retrieve username for message
        users = execute_read("SELECT username FROM users WHERE id = ? AND role = 'HR'", [user_id])
        if not users:
            messages.error(request, "HR Manager not found.")
            return redirect('admin_module:manage_hr')
        
        username = users[0]['username']
        execute_write("DELETE FROM users WHERE id = ?", [user_id])
        messages.success(request, f"HR Manager '{username}' deleted successfully.")
        
    return redirect('admin_module:manage_hr')
