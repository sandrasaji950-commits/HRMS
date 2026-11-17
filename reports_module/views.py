import datetime
from django.shortcuts import render
from smart_hrms.db import execute_read

def employee_report(request):
    """Generate Employee report with filters (department, status)."""
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    query = """
        SELECT e.*, d.department_name, u.username, u.plain_password
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN users u ON e.user_id = u.id
        WHERE 1=1
    """
    params = []

    if dept_filter:
        query += " AND e.department_id = ?"
        params.append(dept_filter)

    if status_filter:
        query += " AND e.status = ?"
        params.append(status_filter)

    query += " ORDER BY e.joining_date DESC"
    
    employees = execute_read(query, params)
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    return render(request, 'reports/employee_report.html', {
        'employees': employees,
        'departments': departments,
        'selected_dept': dept_filter,
        'selected_status': status_filter
    })

def attendance_report(request):
    """Generate Attendance report with filters (start/end dates, department, status)."""
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    query = """
        SELECT a.*, e.first_name, e.last_name, e.designation, d.department_name
        FROM attendance a
        INNER JOIN employees e ON a.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND a.attendance_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND a.attendance_date <= ?"
        params.append(end_date)
    if dept_filter:
        query += " AND e.department_id = ?"
        params.append(dept_filter)
    if status_filter:
        query += " AND a.attendance_status = ?"
        params.append(status_filter)

    query += " ORDER BY a.attendance_date DESC, e.first_name ASC"
    
    attendance_records = execute_read(query, params)
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    return render(request, 'reports/attendance_report.html', {
        'attendance_records': attendance_records,
        'departments': departments,
        'start_date': start_date,
        'end_date': end_date,
        'selected_dept': dept_filter,
        'selected_status': status_filter
    })

def leave_report(request):
    """Generate Leave requests report with filters (start/end dates, leave type, status)."""
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    type_filter = request.GET.get('leave_type', '').strip()
    status_filter = request.GET.get('status', '').strip()

    query = """
        SELECT l.*, e.first_name, e.last_name, e.designation, d.department_name
        FROM leave_requests l
        INNER JOIN employees e ON l.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND l.start_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND l.end_date <= ?"
        params.append(end_date)
    if type_filter:
        query += " AND l.leave_type = ?"
        params.append(type_filter)
    if status_filter:
        query += " AND l.status = ?"
        params.append(status_filter)

    query += " ORDER BY l.start_date DESC"
    
    leaves = execute_read(query, params)

    return render(request, 'reports/leave_report.html', {
        'leaves': leaves,
        'start_date': start_date,
        'end_date': end_date,
        'selected_type': type_filter,
        'selected_status': status_filter
    })
