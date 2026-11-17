from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from smart_hrms.db import execute_read, execute_write

def login_view(request):
    """Log in user and establish custom session."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'accounts/login.html')

        # Retrieve user with raw SQL query
        users = execute_read("SELECT * FROM users WHERE username = ?", [username])
        if users:
            user = users[0]
            # Check password hash securely
            if check_password(password, user['password_hash']):
                # Save session data
                request.session['user_id'] = user['id']
                request.session['username'] = user['username']
                request.session['role'] = user['role']

                # Redirect to appropriate dashboard
                messages.success(request, f"Welcome back, {user['username']}!")
                if user['role'] == 'Admin':
                    return redirect('admin_module:dashboard')
                elif user['role'] == 'HR':
                    return redirect('hr_module:dashboard')
                else:
                    return redirect('employee_module:dashboard')
        
        messages.error(request, "Invalid username or password.")
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """Invalidate session and log user out."""
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')

def change_password_view(request):
    """Allow logged-in user to change their password."""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not old_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, "New password and confirmation password do not match.")
            return render(request, 'accounts/change_password.html')

        # Password strength validation: minimum 8 characters
        if len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return render(request, 'accounts/change_password.html')

        # Fetch current user details
        user_id = request.user_id
        users = execute_read("SELECT * FROM users WHERE id = ?", [user_id])
        
        if users:
            user = users[0]
            if check_password(old_password, user['password_hash']):
                new_hash = make_password(new_password)
                # Update both hash and plain password (plain_password stored as requested by user feedback)
                # TODO(security): Storing plain passwords for Admin visibility as requested. In production, remove plain_password.
                execute_write(
                    "UPDATE users SET password_hash = ?, plain_password = ? WHERE id = ?",
                    [new_hash, new_password, user_id]
                )
                messages.success(request, "Password changed successfully.")
                return redirect('accounts:login')  # Force re-login after password change
            else:
                messages.error(request, "Incorrect old password.")
        else:
            messages.error(request, "User session not found.")
            return redirect('accounts:login')

    return render(request, 'accounts/change_password.html')
