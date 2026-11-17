from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from smart_hrms.db import execute_read, execute_write, init_db
import datetime

class HRMSTests(TestCase):
    def setUp(self):
        """Set up fresh database tables and default admin seed for each test."""
        init_db()
        self.client = Client()

    def test_login_success(self):
        """Test authentication login workflow with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'admin123'
        })
        # Check redirect to Admin Dashboard
        self.assertRedirects(response, reverse('admin_module:dashboard'))
        self.assertEqual(self.client.session['username'], 'admin')
        self.assertEqual(self.client.session['role'], 'Admin')

    def test_login_failure(self):
        """Test authentication login with invalid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Render login template again
        self.assertNotIn('username', self.client.session)

    def test_department_crud(self):
        """Test Department CRUD actions."""
        # 1. Add Department
        dept_data = {
            'department_name': 'Quality Assurance',
            'department_code': 'QA',
            'description': 'Software verification division'
        }
        # Simulate Admin login
        session = self.client.session
        session['user_id'] = 1
        session['username'] = 'admin'
        session['role'] = 'Admin'
        session.save()

        response = self.client.post(reverse('department_module:add'), dept_data)
        self.assertRedirects(response, reverse('department_module:list'))

        # Check DB insert
        depts = execute_read("SELECT * FROM departments WHERE department_code = 'QA'")
        self.assertEqual(len(depts), 1)
        dept_id = depts[0]['department_id']

        # 2. Edit Department
        edit_data = {
            'department_name': 'QA & Testing',
            'department_code': 'QAT',
            'description': 'Updated description'
        }
        response = self.client.post(reverse('department_module:edit', args=[dept_id]), edit_data)
        self.assertRedirects(response, reverse('department_module:list'))
        
        depts_updated = execute_read("SELECT * FROM departments WHERE department_id = ?", [dept_id])
        self.assertEqual(depts_updated[0]['department_code'], 'QAT')
        self.assertEqual(depts_updated[0]['department_name'], 'QA & Testing')

        # 3. Delete Department
        response = self.client.post(reverse('department_module:delete', args=[dept_id]))
        self.assertRedirects(response, reverse('department_module:list'))
        
        depts_deleted = execute_read("SELECT * FROM departments WHERE department_id = ?", [dept_id])
        self.assertEqual(len(depts_deleted), 0)

    def test_employee_crud(self):
        """Test Employee and linked User account CRUD actions."""
        # Setup Admin session
        session = self.client.session
        session['user_id'] = 1
        session['username'] = 'admin'
        session['role'] = 'Admin'
        session.save()

        # Add department first
        dept_id, _ = execute_write(
            "INSERT INTO departments (department_name, department_code) VALUES (?, ?)",
            ['Research', 'RES']
        )

        # 1. Add Employee
        emp_data = {
            'username': 'tester',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'tester@company.com',
            'phone': '1234567890',
            'gender': 'Male',
            'joining_date': '2026-01-01',
            'designation': 'QA Engineer',
            'department_id': dept_id,
            'status': 'Active'
        }

        response = self.client.post(reverse('hr_module:add_employee'), emp_data)
        self.assertRedirects(response, reverse('hr_module:manage_employees'))

        # Verify linked User and Employee DB inserts
        users = execute_read("SELECT * FROM users WHERE username = 'tester'")
        self.assertEqual(len(users), 1)
        user_id = users[0]['id']

        employees = execute_read("SELECT * FROM employees WHERE user_id = ?", [user_id])
        self.assertEqual(len(employees), 1)
        employee_id = employees[0]['employee_id']

        # 2. Edit Employee
        edit_data = {
            'username': 'tester_updated',
            'password': '', # Leave blank to keep current
            'first_name': 'Test',
            'last_name': 'User-Modified',
            'email': 'tester_new@company.com',
            'phone': '0987654321',
            'gender': 'Male',
            'joining_date': '2026-01-01',
            'designation': 'Senior QA Engineer',
            'department_id': dept_id,
            'status': 'Active'
        }
        response = self.client.post(reverse('hr_module:edit_employee', args=[employee_id]), edit_data)
        self.assertRedirects(response, reverse('hr_module:manage_employees'))

        employees_updated = execute_read("SELECT * FROM employees WHERE employee_id = ?", [employee_id])
        self.assertEqual(employees_updated[0]['last_name'], 'User-Modified')
        self.assertEqual(employees_updated[0]['designation'], 'Senior QA Engineer')

        # 3. Delete Employee
        response = self.client.post(reverse('hr_module:delete_employee', args=[employee_id]))
        self.assertRedirects(response, reverse('hr_module:manage_employees'))
        
        # Verify user and employee are deleted
        self.assertEqual(len(execute_read("SELECT * FROM employees WHERE employee_id = ?", [employee_id])), 0)
        self.assertEqual(len(execute_read("SELECT * FROM users WHERE id = ?", [user_id])), 0)

    def test_attendance_mark_and_validation(self):
        """Test Employee attendance marking constraint validations."""
        # Seed an employee user
        pass_hash = make_password('emp12345')
        user_id, _ = execute_write(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ['employee_test', pass_hash, 'Employee']
        )
        dept_id, _ = execute_write("INSERT INTO departments (department_name, department_code) VALUES (?, ?)", ['Research', 'RES'])
        employee_id, _ = execute_write(
            "INSERT INTO employees (user_id, first_name, last_name, email, joining_date, designation, department_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [user_id, 'Emp', 'Test', 'emp@company.com', '2026-01-01', 'Developer', dept_id]
        )

        # Log in as Employee
        session = self.client.session
        session['user_id'] = user_id
        session['username'] = 'employee_test'
        session['role'] = 'Employee'
        session.save()

        # 1. Mark Attendance
        response = self.client.post(reverse('attendance_module:mark'), {
            'attendance_status': 'Present'
        })
        self.assertRedirects(response, reverse('attendance_module:mark'))

        today_str = datetime.date.today().isoformat()
        attendance_logs = execute_read(
            "SELECT * FROM attendance WHERE employee_id = ? AND attendance_date = ?",
            [employee_id, today_str]
        )
        self.assertEqual(len(attendance_logs), 1)

        # 2. Try marking again (should reject / warning redirect)
        response_duplicate = self.client.post(reverse('attendance_module:mark'), {
            'attendance_status': 'Present'
        })
        self.assertRedirects(response_duplicate, reverse('attendance_module:mark'))
        
        # Count should remain 1
        attendance_count = execute_read(
            "SELECT COUNT(*) as count FROM attendance WHERE employee_id = ? AND attendance_date = ?",
            [employee_id, today_str]
        )[0]['count']
        self.assertEqual(attendance_count, 1)

    def test_leave_workflow_and_validation(self):
        """Test Leave application constraints and approval workflow integration."""
        # Seed Employee
        pass_hash = make_password('emp12345')
        user_id, _ = execute_write(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ['employee_test', pass_hash, 'Employee']
        )
        dept_id, _ = execute_write("INSERT INTO departments (department_name, department_code) VALUES (?, ?)", ['Research', 'RES'])
        employee_id, _ = execute_write(
            "INSERT INTO employees (user_id, first_name, last_name, email, joining_date, designation, department_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [user_id, 'Emp', 'Test', 'emp@company.com', '2026-01-01', 'Developer', dept_id]
        )

        # Log in as Employee
        session = self.client.session
        session['user_id'] = user_id
        session['username'] = 'employee_test'
        session['role'] = 'Employee'
        session.save()

        # 1. Apply Leave (Invalid Date - past start date)
        response_invalid = self.client.post(reverse('leave_module:apply'), {
            'leave_type': 'Sick Leave',
            'start_date': '2025-01-01',
            'end_date': '2025-01-05',
            'reason': 'Illness'
        })
        self.assertEqual(response_invalid.status_code, 200) # Re-renders form due to error

        # 2. Apply Leave (Valid)
        tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        after_tomorrow_str = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        
        response_valid = self.client.post(reverse('leave_module:apply'), {
            'leave_type': 'Casual Leave',
            'start_date': tomorrow_str,
            'end_date': after_tomorrow_str,
            'reason': 'Family vacation'
        })
        self.assertRedirects(response_valid, reverse('leave_module:history'))

        # Check DB record
        leaves = execute_read("SELECT * FROM leave_requests WHERE employee_id = ?", [employee_id])
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0]['status'], 'Pending')
        leave_id = leaves[0]['leave_id']

        # 3. Log in as HR Manager to approve leave
        session = self.client.session
        session['user_id'] = 2
        session['username'] = 'hr_manager'
        session['role'] = 'HR'
        session.save()

        response_approve = self.client.post(reverse('leave_module:action', args=[leave_id, 'approve']))
        self.assertRedirects(response_approve, reverse('leave_module:manage'))

        # Check DB status updated to Approved
        leaves_approved = execute_read("SELECT * FROM leave_requests WHERE leave_id = ?", [leave_id])
        self.assertEqual(leaves_approved[0]['status'], 'Approved')
