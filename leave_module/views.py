import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from smart_hrms.db import execute_read, execute_write

def get_employee_by_user_id(user_id):
    """Fetch employee record associated with a user ID."""
    emps = execute_read("SELECT * FROM employees WHERE user_id = ?", [user_id])
    return emps[0] if emps else None

def apply_leave(request):
    """Allow employee to submit a leave request."""
    employee = get_employee_by_user_id(request.user_id)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('accounts:login')

    employee_id = employee['employee_id']

    if request.method == 'POST':
        leave_type = request.POST.get('leave_type', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        reason = request.POST.get('reason', '').strip()

        if not leave_type or not start_date or not end_date:
            messages.error(request, "Leave Type, Start Date, and End Date are required.")
            return render(request, 'leave/apply_leave.html')

        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return render(request, 'leave/apply_leave.html')

        if start_dt < datetime.date.today():
            messages.error(request, "Start date cannot be in the past.")
            return render(request, 'leave/apply_leave.html')

        if end_dt < start_dt:
            messages.error(request, "End date must be on or after start date.")
            return render(request, 'leave/apply_leave.html')

        # Insert leave request
        execute_write(
            "INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status) VALUES (?, ?, ?, ?, ?, ?)",
            [employee_id, leave_type, start_date, end_date, reason, 'Pending']
        )
        messages.success(request, "Leave request submitted successfully.")
        return redirect('leave_module:history')

    return render(request, 'leave/apply_leave.html')

def leave_history(request):
    """Display leave request history for the logged-in employee."""
    employee = get_employee_by_user_id(request.user_id)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('accounts:login')

    leaves = execute_read(
        "SELECT * FROM leave_requests WHERE employee_id = ? ORDER BY start_date DESC",
        [employee['employee_id']]
    )
    return render(request, 'leave/leave_history.html', {'leaves': leaves})

def manage_leaves(request):
    """Allow HR/Admin to review all pending and past leave applications."""
    status_filter = request.GET.get('status', 'Pending').strip()
    search_query = request.GET.get('search', '').strip()

    query = """
        SELECT l.*, e.first_name, e.last_name, d.department_name, e.designation
        FROM leave_requests l
        INNER JOIN employees e ON l.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND l.status = ?"
        params.append(status_filter)

    if search_query:
        query += " AND (e.first_name LIKE ? OR e.last_name LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term])

    query += " ORDER BY l.start_date DESC"
    leaves = execute_read(query, params)

    return render(request, 'leave/manage_leaves.html', {
        'leaves': leaves,
        'selected_status': status_filter,
        'search_query': search_query
    })

def leave_action(request, leave_id, action_type):
    """Approve or reject a leave request (HR/Admin only)."""
    if request.method == 'POST':
        # Verify request exists
        leaves = execute_read("SELECT * FROM leave_requests WHERE leave_id = ?", [leave_id])
        if not leaves:
            messages.error(request, "Leave request not found.")
            return redirect('leave_module:manage')

        new_status = 'Approved' if action_type == 'approve' else 'Rejected'
        execute_write("UPDATE leave_requests SET status = ? WHERE leave_id = ?", [new_status, leave_id])
        messages.success(request, f"Leave request status updated to '{new_status}' successfully.")

    return redirect('leave_module:manage')
