# Admin Portal

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The Admin Portal is the central operational management system of the University of Global Village Smart ERP.

While the Super Admin is responsible for overall system administration and configuration, the Admin manages the day-to-day academic and administrative operations of the university.

The Admin Portal serves as the bridge between academic, student, finance, and examination modules.

Its primary objective is to ensure that university operations remain organized, synchronized, and efficient.

---

# 2. Objectives

The Admin Portal is designed to allow administrators to:

- Manage academic structures
- Manage students
- Manage faculty
- Manage departments
- Monitor university activities
- Configure academic sessions
- Publish notices
- Monitor system statistics
- Coordinate between departments

---

# 3. Current Status

Development Status

🟡 Partially Completed

Completed

✓ Dashboard

✓ User Management

✓ Department Management

✓ Semester Management

✓ Batch Management

✓ Course Management

✓ Course Offering Management

Remaining

- Analytics
- Reports
- Student Promotion
- Bulk Operations
- Academic Calendar
- System Monitoring

---

# 4. Dashboard

The Admin Dashboard provides an overview of university operations.

Dashboard Cards

- Total Students
- Total Faculty
- Departments
- Running Courses
- Active Batches
- Notices
- Applications
- Pending Requests

Quick Actions

- Add Student
- Add Faculty
- Add Department
- Create Course
- Publish Notice

---

# 5. User Management

The Admin can manage all university users except Super Admin accounts.

Supported users

- Students
- Faculty
- Department Heads
- Accounts Officers
- Exam Controllers

Functions

- Create user
- Edit user
- Activate account
- Deactivate account
- Reset password
- Assign role

Future

- Bulk user creation
- Import users
- Export users

---

# 6. Student Management

The Admin manages student records throughout their academic lifecycle.

Current Features

- Create students
- Edit student information
- Assign department
- Assign batch
- Assign semester
- Assign section

Future Features

- Student promotion
- Semester progression
- Transfer students
- Graduation processing
- Alumni conversion

---

# 7. Faculty Management

Faculty information is maintained by the Admin.

Current Features

- Create faculty
- Edit faculty
- Assign department
- Employee information
- Faculty account management

Future

- Teaching load analysis
- Faculty performance
- Office hours
- Leave management

---

# 8. Department Management

Departments represent the primary academic units.

Current Features

- Create department
- Edit department
- Department codes
- Department status

Future

- Department statistics
- Budget allocation
- Department reports

---

# 9. Semester Management

The Admin manages semester definitions.

Current Features

- Create semester
- Edit semester
- Activate semester

Current Structure

Semester 1

↓

Semester 8

Future

Automatic semester progression.

---

# 10. Batch Management

Batches represent admission sessions.

Current Timeline

Winter 2023

↓

Summer 2026

Semester Mapping

Winter 2023 → Semester 8

Summer 2023 → Semester 7

Winter 2024 → Semester 6

Summer 2024 → Semester 5

Winter 2025 → Semester 4

Summer 2025 → Semester 3

Winter 2026 → Semester 2

Summer 2026 → Semester 1

Future

Automatic yearly batch creation.

---

# 11. Course Management

Courses define the university curriculum.

Current Features

- Create course
- Edit course
- Credits
- Semester assignment
- Department assignment

Testing Dataset

Complete curriculum added for

- CSE
- EEE
- Civil Engineering
- English
- BBA
- Law
- Pharmacy

Future

Course prerequisites

Electives

Course versioning

---

# 12. Course Offering Management

Course Offering is the most important academic entity.

Current Features

Assign

- Faculty
- Batch
- Semester
- Section

Testing Dataset

Every active course has

Section A

Section B

Faculty assigned

Future

Automatic offering generation.

---

# 13. Notice Management

Admins can publish notices.

Target Audience

- Students
- Faculty
- Accounts
- Exam Controller
- Department Head
- Everyone

Future

Scheduled publishing

Attachments

Priority notices

---

# 14. Academic Monitoring

Future dashboard widgets

Students per department

Faculty workload

Course distribution

Semester statistics

Enrollment trends

---

# 15. Reports

Planned Reports

Student reports

Faculty reports

Course reports

Department reports

Semester reports

Enrollment reports

Graduation reports

Drop reports

Export

PDF

Excel

CSV

---

# 16. Bulk Operations

Future module

Bulk student creation

Bulk faculty creation

Bulk course creation

Bulk semester registration

Bulk promotion

Bulk section assignment

Bulk graduation

---

# 17. Academic Calendar

Future module

Semester start

Semester end

Registration

Midterm

Final

Vacations

Public holidays

---

# 18. Student Promotion

Future workflow

Semester End

↓

Calculate Results

↓

Promote Eligible Students

↓

Update Semester

↓

Generate New Course Registrations

↓

Archive Previous Semester

---

# 19. Analytics

Planned Dashboard

Admissions

Department growth

Gender distribution

Pass rates

Attendance trends

Financial overview

Faculty workload

Course popularity

Student performance

---

# 20. Integration

The Admin Portal connects directly with

Academics

↓

Students

↓

Faculty

↓

Finance

↓

Examinations

↓

Notices

↓

Applications

It serves as the administrative control center for the ERP.

---

# 21. Current Mock Dataset

The Admin module currently manages a realistic testing environment.

Dataset includes

✓ Departments

✓ Semesters

✓ Batches

✓ Faculty

✓ Courses

✓ Course Offerings

✓ Students

✓ Course Registrations

This dataset allows end-to-end workflow testing.

---

# 22. Security

The Admin Portal enforces

- Login required
- Role verification
- Permission checks
- Department validation
- Object ownership
- CSRF protection

Admins cannot perform Super Admin configuration tasks.

---

# 23. Future Improvements

The Admin Portal will continue expanding with

- Academic calendar
- Promotion engine
- Graduation processing
- Alumni conversion
- Advanced reports
- Bulk import/export
- Analytics dashboard
- Notification center
- Audit logs
- Workflow approvals

---

# 24. Long-Term Vision

The Admin Portal is intended to become the operational headquarters of the university.

While specialized users (Faculty, Accounts, Exam Controller, Department Heads) manage their own responsibilities, the Admin Portal oversees and coordinates the institution as a whole.

The final system will enable administrators to monitor academic activities, student progress, faculty operations, and institutional performance from a single centralized interface while maintaining clear separation of responsibilities through role-based access control.