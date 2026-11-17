from django.shortcuts import render, redirect
from django.contrib import messages
from smart_hrms.db import execute_read, execute_write

def department_list(request):
    if not request.session.get('username'):
        return redirect('accounts:login')
    """List all departments with optional search functionality."""
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Search by department name or code
        departments = execute_read(
            "SELECT * FROM departments WHERE department_name LIKE ? OR department_code LIKE ? ORDER BY department_name",
            [f"%{search_query}%", f"%{search_query}%"]
        )
    else:
        departments = execute_read("SELECT * FROM departments ORDER BY department_name")
        
    return render(request, 'department/department_list.html', {
        'departments': departments,
        'search_query': search_query
    })

def add_department(request):
    if not request.session.get('username'):
        return redirect('accounts:login')
    """Add a new department."""
    if request.method == 'POST':
        name = request.POST.get('department_name', '').strip()
        code = request.POST.get('department_code', '').strip().upper()
        description = request.POST.get('description', '').strip()

        if not name or not code:
            messages.error(request, "Department Name and Code are required.")
            return render(request, 'department/add_department.html')

        # Check uniqueness of code
        existing = execute_read("SELECT * FROM departments WHERE department_code = ?", [code])
        if existing:
            messages.error(request, f"Department with Code '{code}' already exists.")
            return render(request, 'department/add_department.html', {
                'department_name': name,
                'description': description
            })

        # Insert using raw SQL
        execute_write(
            "INSERT INTO departments (department_name, department_code, description) VALUES (?, ?, ?)",
            [name, code, description]
        )
        messages.success(request, f"Department '{name}' added successfully.")
        return redirect('department_module:list')

    return render(request, 'department/add_department.html')

def edit_department(request, department_id):
    if not request.session.get('username'):
        return redirect('accounts:login')
    """Edit an existing department."""
    # Retrieve department
    deps = execute_read("SELECT * FROM departments WHERE department_id = ?", [department_id])
    if not deps:
        messages.error(request, "Department not found.")
        return redirect('department_module:list')
    department = deps[0]

    if request.method == 'POST':
        name = request.POST.get('department_name', '').strip()
        code = request.POST.get('department_code', '').strip().upper()
        description = request.POST.get('description', '').strip()

        if not name or not code:
            messages.error(request, "Department Name and Code are required.")
            return render(request, 'department/edit_department.html', {'department': department})

        # Check uniqueness of code (excluding current department)
        existing = execute_read(
            "SELECT * FROM departments WHERE department_code = ? AND department_id != ?",
            [code, department_id]
        )
        if existing:
            messages.error(request, f"Department with Code '{code}' already exists.")
            return render(request, 'department/edit_department.html', {
                'department': {
                    'department_id': department_id,
                    'department_name': name,
                    'department_code': code,
                    'description': description
                }
            })

        # Update using raw SQL
        execute_write(
            "UPDATE departments SET department_name = ?, department_code = ?, description = ? WHERE department_id = ?",
            [name, code, description, department_id]
        )
        messages.success(request, f"Department '{name}' updated successfully.")
        return redirect('department_module:list')

    return render(request, 'department/edit_department.html', {'department': department})

def delete_department(request, department_id):
    if not request.session.get('username'):
        return redirect('accounts:login')
    """Delete a department."""
    if request.method == 'POST':
        # Check if department exists
        deps = execute_read("SELECT * FROM departments WHERE department_id = ?", [department_id])
        if not deps:
            messages.error(request, "Department not found.")
            return redirect('department_module:list')
        
        # Check if employees are assigned to this department
        employees = execute_read("SELECT COUNT(*) as count FROM employees WHERE department_id = ?", [department_id])
        if employees[0]['count'] > 0:
            messages.error(request, "Cannot delete department: Employees are currently assigned to it.")
            return redirect('department_module:list')

        # Delete department using raw SQL
        execute_write("DELETE FROM departments WHERE department_id = ?", [department_id])
        messages.success(request, "Department deleted successfully.")
    
    return redirect('department_module:list')
