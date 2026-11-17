import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from smart_hrms.db import execute_read, execute_write

def get_logged_in_employee(user_id):
    """Retrieve employee record linked to the logged-in user."""
    emps = execute_read(
        """SELECT e.*, d.department_name, u.username 
        FROM employees e 
        LEFT JOIN departments d ON e.department_id = d.department_id 
        LEFT JOIN users u ON e.user_id = u.id 
        WHERE e.user_id = ?""",
        [user_id]
    )
    return emps[0] if emps else None

def employee_dashboard(request):
    """Render Employee dashboard containing attendance status and leave requests count."""
    employee = get_logged_in_employee(request.user_id)
    
    if not employee:
        messages.error(request, "Employee profile not found.")
        return render(request, 'employee/dashboard.html', {'error': 'Profile not found'})

    employee_id = employee['employee_id']
    today_str = datetime.date.today().isoformat()

    # Today's attendance status
    attendance = execute_read(
        "SELECT * FROM attendance WHERE employee_id = ? AND attendance_date = ?",
        [employee_id, today_str]
    )
    today_attendance = attendance[0] if attendance else None

    # Leave history stats
    leave_count = execute_read(
        "SELECT COUNT(*) as count FROM leave_requests WHERE employee_id = ?",
        [employee_id]
    )[0]['count']

    pending_leaves = execute_read(
        "SELECT COUNT(*) as count FROM leave_requests WHERE employee_id = ? AND status = 'Pending'",
        [employee_id]
    )[0]['count']

    return render(request, 'employee/dashboard.html', {
        'employee': employee,
        'today_attendance': today_attendance,
        'leave_count': leave_count,
        'pending_leaves': pending_leaves
    })

def employee_profile(request):
    """Allow employee to view and edit limited profile details (phone, email)."""
    employee = get_logged_in_employee(request.user_id)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('accounts:login')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not email:
            messages.error(request, "Email address is required.")
            return render(request, 'employee/profile.html', {'employee': employee})

        # Check email uniqueness (excluding current employee)
        existing_email = execute_read(
            "SELECT * FROM employees WHERE email = ? AND employee_id != ?",
            [email, employee['employee_id']]
        )
        if existing_email:
            messages.error(request, "Email address is already in use by another employee.")
            return render(request, 'employee/profile.html', {'employee': employee})

        # Update details in the database
        execute_write(
            "UPDATE employees SET email = ?, phone = ? WHERE employee_id = ?",
            [email, phone, employee['employee_id']]
        )
        messages.success(request, "Profile updated successfully.")
        return redirect('employee_module:profile')

    return render(request, 'employee/profile.html', {'employee': employee})
