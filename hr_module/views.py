import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from smart_hrms.db import execute_read, execute_write

def hr_dashboard(request):
    """Render HR dashboard with relevant statistics."""
    # Count of active employees
    emp_count = execute_read("SELECT COUNT(*) as count FROM employees WHERE status = 'Active'")[0]['count']
    
    # Today's date in YYYY-MM-DD format
    today_str = datetime.date.today().isoformat()
    
    # Today's present count
    present_count = execute_read(
        "SELECT COUNT(*) as count FROM attendance WHERE attendance_date = ? AND attendance_status = 'Present'",
        [today_str]
    )[0]['count']
    
    # Pending leave requests count
    pending_leaves = execute_read("SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'")[0]['count']

    return render(request, 'hr/dashboard.html', {
        'total_employees': emp_count,
        'today_attendance': present_count,
        'pending_requests': pending_leaves
    })

def manage_employees(request):
    """List employees with optional filters (search, department, status)."""
    search_query = request.GET.get('search', '').strip()
    dept_filter = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', '').strip()

    # Query to fetch employees with department details
    query = """
        SELECT e.*, d.department_name, u.username, u.plain_password
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN users u ON e.user_id = u.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.email LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    if dept_filter:
        query += " AND e.department_id = ?"
        params.append(dept_filter)

    if status_filter:
        query += " AND e.status = ?"
        params.append(status_filter)

    query += " ORDER BY e.employee_id DESC"

    employees = execute_read(query, params)
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    return render(request, 'hr/manage_employees.html', {
        'employees': employees,
        'departments': departments,
        'search_query': search_query,
        'selected_dept': dept_filter,
        'selected_status': status_filter
    })

def add_employee(request):
    """Add a new employee and create their linked user account."""
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    if request.method == 'POST':
        # User details
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Employee details
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        joining_date = request.POST.get('joining_date', '').strip()
        designation = request.POST.get('designation', '').strip()
        department_id = request.POST.get('department_id', '').strip()
        status = request.POST.get('status', 'Active').strip()

        # Validate required fields
        if not (username and password and first_name and last_name and email and joining_date and designation and department_id):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'hr/add_employee.html', {'departments': departments, 'form_data': request.POST})

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'hr/add_employee.html', {'departments': departments, 'form_data': request.POST})

        # Check unique constraints
        existing_username = execute_read("SELECT * FROM users WHERE username = ?", [username])
        if existing_username:
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'hr/add_employee.html', {'departments': departments, 'form_data': request.POST})

        existing_email = execute_read("SELECT * FROM employees WHERE email = ?", [email])
        if existing_email:
            messages.error(request, f"Employee with email '{email}' already exists.")
            return render(request, 'hr/add_employee.html', {'departments': departments, 'form_data': request.POST})

        # Create user account in users table
        password_hash = make_password(password)
        # TODO(security): Storing plain passwords for Admin visibility as requested. In production, remove plain_password.
        user_id, _ = execute_write(
            "INSERT INTO users (username, password_hash, plain_password, role) VALUES (?, ?, ?, ?)",
            [username, password_hash, password, 'Employee']
        )

        # Create employee record linked to the user account
        execute_write(
            """INSERT INTO employees 
            (user_id, first_name, last_name, email, phone, gender, joining_date, designation, department_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [user_id, first_name, last_name, email, phone, gender, joining_date, designation, department_id, status]
        )

        messages.success(request, f"Employee '{first_name} {last_name}' added successfully.")
        return redirect('hr_module:manage_employees')

    return render(request, 'hr/add_employee.html', {'departments': departments})

def edit_employee(request, employee_id):
    """Edit employee details and linked user account."""
    departments = execute_read("SELECT * FROM departments ORDER BY department_name")

    # Fetch employee
    emps = execute_read("SELECT * FROM employees WHERE employee_id = ?", [employee_id])
    if not emps:
        messages.error(request, "Employee not found.")
        return redirect('hr_module:manage_employees')
    employee = emps[0]

    # Fetch user account details
    user = None
    if employee['user_id']:
        users = execute_read("SELECT * FROM users WHERE id = ?", [employee['user_id']])
        if users:
            user = users[0]

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        joining_date = request.POST.get('joining_date', '').strip()
        designation = request.POST.get('designation', '').strip()
        department_id = request.POST.get('department_id', '').strip()
        status = request.POST.get('status', 'Active').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not (first_name and last_name and email and joining_date and designation and department_id and username):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'hr/edit_employee.html', {
                'departments': departments,
                'employee': employee,
                'user': user
            })

        # Check email uniqueness (excluding current employee)
        existing_email = execute_read(
            "SELECT * FROM employees WHERE email = ? AND employee_id != ?",
            [email, employee_id]
        )
        if existing_email:
            messages.error(request, f"Email '{email}' is already in use by another employee.")
            return render(request, 'hr/edit_employee.html', {
                'departments': departments,
                'employee': employee,
                'user': user
            })

        # Update user account
        if employee['user_id']:
            existing_username = execute_read(
                "SELECT * FROM users WHERE username = ? AND id != ?",
                [username, employee['user_id']]
            )
            if existing_username:
                messages.error(request, f"Username '{username}' is already taken.")
                return render(request, 'hr/edit_employee.html', {
                    'departments': departments,
                    'employee': employee,
                    'user': user
                })

            if password:
                if len(password) < 8:
                    messages.error(request, "Password must be at least 8 characters long.")
                    return render(request, 'hr/edit_employee.html', {
                        'departments': departments,
                        'employee': employee,
                        'user': user
                    })
                password_hash = make_password(password)
                # TODO(security): Storing plain passwords for Admin visibility as requested. In production, remove plain_password.
                execute_write(
                    "UPDATE users SET username = ?, password_hash = ?, plain_password = ? WHERE id = ?",
                    [username, password_hash, password, employee['user_id']]
                )
            else:
                execute_write("UPDATE users SET username = ? WHERE id = ?", [username, employee['user_id']])

        # Update employee record
        execute_write(
            """UPDATE employees SET 
            first_name = ?, last_name = ?, email = ?, phone = ?, gender = ?, 
            joining_date = ?, designation = ?, department_id = ?, status = ?
            WHERE employee_id = ?""",
            [first_name, last_name, email, phone, gender, joining_date, designation, department_id, status, employee_id]
        )

        messages.success(request, f"Employee '{first_name} {last_name}' updated successfully.")
        return redirect('hr_module:manage_employees')

    return render(request, 'hr/edit_employee.html', {
        'departments': departments,
        'employee': employee,
        'user': user
    })

def delete_employee(request, employee_id):
    """Delete employee and their linked user account."""
    if request.method == 'POST':
        emps = execute_read("SELECT first_name, last_name, user_id FROM employees WHERE employee_id = ?", [employee_id])
        if not emps:
            messages.error(request, "Employee not found.")
            return redirect('hr_module:manage_employees')
        
        employee = emps[0]
        
        # Delete user account first (will set employee.user_id to null or cascade correctly)
        if employee['user_id']:
            execute_write("DELETE FROM users WHERE id = ?", [employee['user_id']])
            
        # Delete employee record
        execute_write("DELETE FROM employees WHERE employee_id = ?", [employee_id])
        
        messages.success(request, f"Employee '{employee['first_name']} {employee['last_name']}' deleted successfully.")
        
    return redirect('hr_module:manage_employees')
