# User Management Module

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The User Management module controls every user account within the UGV Smart University Portal.

Every person who logs into the system is represented by a User Account.

The module manages

- Authentication
- Authorization
- User Creation
- Role Assignment
- Password Management
- Profile Management
- Account Activation
- Bulk Import

This module is the entry point of the ERP.

---

# 2. Current Status

Development Status

🟢 Mostly Complete

Completed

✓ Custom User Model

✓ Multiple Roles

✓ Login System

✓ Logout

✓ Password Hashing

✓ Bulk Student Upload

✓ Faculty Creation

✓ Accounts Users

✓ Department Heads

✓ Role-based Redirect

✓ Dashboard Access Control

Remaining

- Password reset email
- User activity history
- Two-factor authentication
- Profile photo upload
- LDAP support

---

# 3. User Roles

Current supported roles

```

Super Admin
↓
Admin
↓
Faculty
↓
Department Head
↓
Accounts Officer
↓
Exam Controller
↓
Student

```

Each role receives its own dashboard.

---

# 4. Login Flow

```

Login

↓

Authenticate

↓

Determine Role

↓

Redirect

↓

Dashboard

```

Example

Student

↓

Student Dashboard

Faculty

↓

Faculty Dashboard

Accounts

↓

Accounts Dashboard

---

# 5. Authentication

Current authentication uses Django Authentication.

Features

- Username Login
- Password Hashing
- Session Authentication
- CSRF Protection

---

# 6. Bulk Student Upload

One of the largest completed features.

Supports

- CSV Upload
- Automatic User Creation
- Student Profile Creation
- Finance Profile Creation
- Fee Assignment
- Validation
- Duplicate Detection

---

## Automatic Validation

Checks include

✓ Duplicate Username

✓ Duplicate Student ID

✓ Duplicate Email

✓ Missing Batch

✓ Missing Department

✓ Missing Program

✓ Missing Fee Structure

Invalid rows are skipped.

---

# 7. Student ID Design

Student IDs follow a structured 8-digit format.

Format

```

DDDYSSNN

```

Where

DDD

Department Code

Y

Batch Year Identifier

SS

Semester

NN

Serial Number

Example

```

00123101

```

Meaning

Department

001

Winter 2023 Batch

Semester

8

Student

01

Username equals Student ID.

---

# 8. Default Passwords

Current testing password

```

2001

```

Applied to

- Students
- Faculty
- Department Heads
- Accounts Officers
- Exam Controllers

Can be changed after first login in future versions.

---

# 9. Faculty Accounts

Faculty accounts include

- Employee ID
- Department
- Designation
- Username
- Password

Each department currently contains two faculty members for testing.

Faculty 1

Faculty 2

Used during course offering assignment.

---

# 10. Employee IDs

Employee IDs are unique.

Example

```

FAC00101

```

Current testing IDs are department-based.

---

# 11. Permission System

Permissions are role-based.

Example

Student

Can

✓ View Results

✓ Register Courses

Cannot

✗ Edit Courses

✗ Create Users

---

Faculty

Can

✓ Attendance

✓ Marks

✓ Student Lists

Cannot

✗ Create Students

---

Admin

Full access.

---

# 12. Dashboard Routing

Users are automatically redirected after login.

Example

```

Student
→
/student/

Faculty
→
/faculty/

Accounts
→
/accounts/

Exam
→
/exam/

```

---

# 13. Current Testing Dataset

Current mock users

Approximately

373 Students

16 Faculty

Accounts Officer

Exam Controller

Department Heads

Admin

Super Admin

---

# 14. Future Features

Planned improvements

- Password Reset Email
- OTP Login
- MFA
- User Activity Log
- Session History
- Device Tracking
- Last Login Map
- Profile Pictures
- Digital Signature

---

# 15. Related Modules

Connected to

- Academic Setup
- Finance
- Student Portal
- Faculty Portal
- Examination
- Results
- Attendance

Every module depends on User Management.