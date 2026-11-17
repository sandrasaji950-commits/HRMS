import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from smart_hrms.db import execute_read, execute_write

def get_employee_by_user_id(request):
    """Fetch employee record associated with the logged-in user's session ID."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    emps = execute_read("SELECT * FROM employees WHERE user_id = ?", [user_id])
    return emps[0] if emps else None

def mark_attendance(request):
    """Allow logged-in employee to mark attendance for today."""
    if not request.session.get('username'):
        return redirect('accounts:login')
    employee = get_employee_by_user_id(request)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('accounts:login')

    # employee already fetched above
    employee_id = employee['employee_id']
    today_str = datetime.date.today().isoformat()

    # Check if attendance already exists for today
    existing = execute_read(
        "SELECT * FROM attendance WHERE employee_id = ? AND attendance_date = ?",
        [employee_id, today_str]
    )
    today_attendance = existing[0] if existing else None

    # Fetch last 10 attendance records for this employee
    attendance_history = execute_read(
        "SELECT * FROM attendance WHERE employee_id = ? ORDER BY attendance_date DESC LIMIT 10",
        [employee_id]
    )

    if request.method == 'POST':
        if today_attendance:
            messages.warning(request, "You have already marked attendance for today.")
            return redirect('attendance_module:mark')

        status = request.POST.get('attendance_status', 'Present').strip()
        now_time = datetime.datetime.now().strftime("%H:%M:%S")

        # Insert attendance record
        execute_write(
            "INSERT INTO attendance (employee_id, attendance_date, check_in_time, attendance_status) VALUES (?, ?, ?, ?)",
            [employee_id, today_str, now_time, status]
        )
        messages.success(request, f"Attendance marked as '{status}' successfully.")
        return redirect('attendance_module:mark')

    return render(request, 'attendance/attendance.html', {
        'employee': employee,
        'today_attendance': today_attendance,
        'attendance_history': attendance_history
    })

def manage_attendance(request):
    """Allow HR/Admin to view and filter attendance logs."""
    date_filter = request.GET.get('date', datetime.date.today().isoformat()).strip()
    dept_filter = request.GET.get('department', '').strip()
    search_query = request.GET.get('search', '').strip()

    # Query to fetch attendance records with employee and department details
    query = """
        SELECT a.*, e.first_name, e.last_name, d.department_name, e.designation
        FROM attendance a
        INNER JOIN employees e ON a.employee_id = e.employee_id
        LEFT JOIN departments d ON e.department_id = d.department_id
        WHERE 1=1
    """
    params = []

    if date_filter:
        query += " AND a.attendance_date = ?"
        params.append(date_filter)

    if dept_filter:
        query += " AND e.department_id = ?"
        params.append(dept_filter)

    if search_query:
        query += " AND (e.first_name LIKE ? OR e.last_name LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term])

    query += " ORDER BY a.attendance_date DESC, e.first_name ASC"
    
    attendance_records = execute_read(query, params)
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    return render(request, 'attendance/manage_attendance.html', {
        'attendance_records': attendance_records,
        'departments': departments,
        'selected_date': date_filter,
        'selected_dept': dept_filter,
        'search_query': search_query
    })

def add_attendance_record(request):
    """Allow HR/Admin to manually log attendance for any active employee."""
    employees = execute_read("SELECT employee_id, first_name, last_name FROM employees WHERE status = 'Active' ORDER BY first_name")

    if request.method == 'POST':
        employee_id = request.POST.get('employee_id', '').strip()
        date_val = request.POST.get('attendance_date', '').strip()
        check_in = request.POST.get('check_in_time', '').strip() or None
        status = request.POST.get('attendance_status', 'Present').strip()

        if not employee_id or not date_val:
            messages.error(request, "Employee and Attendance Date are required.")
            return render(request, 'attendance/add_attendance.html', {'employees': employees})

        # Check if record already exists for this date
        existing = execute_read(
            "SELECT * FROM attendance WHERE employee_id = ? AND attendance_date = ?",
            [employee_id, date_val]
        )
        if existing:
            messages.error(request, "Attendance record for this employee on this date already exists.")
            return render(request, 'attendance/add_attendance.html', {'employees': employees})

        # Insert record
        execute_write(
            "INSERT INTO attendance (employee_id, attendance_date, check_in_time, attendance_status) VALUES (?, ?, ?, ?)",
            [employee_id, date_val, check_in, status]
        )
        messages.success(request, "Attendance record logged successfully.")
        return redirect('attendance_module:manage')

    return render(request, 'attendance/add_attendance.html', {'employees': employees})

def edit_attendance_record(request, attendance_id):
    """Allow HR/Admin to edit an existing attendance record."""
    records = execute_read(
        """SELECT a.*, e.first_name, e.last_name 
        FROM attendance a 
        INNER JOIN employees e ON a.employee_id = e.employee_id 
        WHERE a.attendance_id = ?""",
        [attendance_id]
    )
    if not records:
        messages.error(request, "Attendance record not found.")
        return redirect('attendance_module:manage')
    
    record = records[0]

    if request.method == 'POST':
        date_val = request.POST.get('attendance_date', '').strip()
        check_in = request.POST.get('check_in_time', '').strip() or None
        status = request.POST.get('attendance_status', '').strip()

        if not date_val or not status:
            messages.error(request, "Date and Attendance Status are required.")
            return render(request, 'attendance/edit_attendance.html', {'record': record})

        # Check duplicate if date changed
        if date_val != record['attendance_date']:
            existing = execute_read(
                "SELECT * FROM attendance WHERE employee_id = ? AND attendance_date = ? AND attendance_id != ?",
                [record['employee_id'], date_val, attendance_id]
            )
            if existing:
                messages.error(request, "Another attendance record for this employee on this date already exists.")
                return render(request, 'attendance/edit_attendance.html', {'record': record})

        # Update record
        execute_write(
            "UPDATE attendance SET attendance_date = ?, check_in_time = ?, attendance_status = ? WHERE attendance_id = ?",
            [date_val, check_in, status, attendance_id]
        )
        messages.success(request, "Attendance record updated successfully.")
        return redirect('attendance_module:manage')

    return render(request, 'attendance/edit_attendance.html', {'record': record})
