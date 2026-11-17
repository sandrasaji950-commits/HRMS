-- Smart HRMS Database Schema
-- SQLite

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    plain_password TEXT, -- TODO(security): Storing plain passwords for Admin visibility as requested by product feedback.
    role TEXT NOT NULL CHECK(role IN ('Admin', 'HR', 'Employee')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL,
    department_code TEXT UNIQUE NOT NULL,
    description TEXT
);

-- Employees Table
CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    joining_date DATE NOT NULL,
    designation TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(department_id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK(status IN ('Active', 'Inactive')) DEFAULT 'Active'
);

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TIME,
    attendance_status TEXT NOT NULL CHECK(attendance_status IN ('Present', 'Absent')),
    UNIQUE(employee_id, attendance_date)
);

-- Leave Requests Table
CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    leave_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status TEXT NOT NULL CHECK(status IN ('Pending', 'Approved', 'Rejected')) DEFAULT 'Pending'
);
