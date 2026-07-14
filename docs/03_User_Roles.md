# User Roles & Permissions

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The UGV Smart University Portal is built around **Role-Based Access Control (RBAC)**.

Every authenticated user belongs to exactly one role, and each role has its own dashboard, permissions, and workflow.

This approach ensures:

- Security
- Simplicity
- Better user experience
- Separation of responsibilities
- Easier maintenance

Instead of exposing every feature to every user, each role only sees the modules required for their responsibilities.

---

# 2. Current User Roles

The system currently supports seven major user roles.

| Role | Purpose |
|--------|----------|
| Super Admin | Complete system administration |
| Admin | University administration |
| Department Head | Department management |
| Faculty | Teaching and academic activities |
| Accounts | Financial management |
| Exam Controller | Examination management |
| Student | Student self-service portal |

---

# 3. Role Hierarchy

```
                    Super Admin
                         │
          ┌──────────────┴──────────────┐
          │                             │
       Admin                     Department Head
          │                             │
     ┌────┴────┐                    Faculty
     │         │
 Accounts   Exam Controller
                 │
              Students
```

Higher-level users can perform broader administrative tasks, while operational users (Faculty, Accounts, Exam Controller) focus on their assigned responsibilities.

---

# 4. Super Admin

## Purpose

The Super Admin manages the entire university portal.

This role has unrestricted access to every module.

---

## Responsibilities

- Create and manage users
- Manage departments
- Configure university settings
- Create semesters
- Create batches
- Manage courses
- Manage academic structure
- Manage notices
- Manage system settings
- View reports
- Configure permissions
- Maintain system integrity

---

## Dashboard Features

- System Overview
- User Management
- Academic Management
- Finance Overview
- Examination Overview
- Reports
- Settings

---

## Permissions

✓ Full Create

✓ Full Read

✓ Full Update

✓ Full Delete

Across every module.

---

# 5. Admin

## Purpose

The Admin manages day-to-day university administration.

Unlike Super Admin, Admin focuses on academic operations rather than system configuration.

---

## Responsibilities

- Manage students
- Manage faculty
- Manage departments
- Create courses
- Create semesters
- Create batches
- Publish notices
- Monitor portal activities

---

## Dashboard Features

- Student Management
- Faculty Management
- Academic Management
- Notices
- Reports

---

## Permissions

✓ Full access to academic modules

Limited access to system configuration.

---

# 6. Department Head

## Purpose

Manages one academic department.

---

## Responsibilities

- Monitor faculty
- Monitor students
- Review department activities
- View reports
- Coordinate academic planning

---

## Dashboard Features

- Department Overview
- Faculty List
- Student List
- Department Reports
- Academic Statistics

---

## Permissions

Department-specific only.

Cannot modify other departments.

---

# 7. Faculty

## Purpose

Faculty members manage teaching activities.

Every faculty member teaches through **Course Offerings**.

---

## Responsibilities

- Take attendance
- Upload course materials
- Publish assignments
- Evaluate submissions
- Submit marks
- View hall duties
- View teaching schedule

---

## Dashboard Features

### Dashboard

Overview of assigned courses.

---

### My Courses

Shows assigned Course Offerings.

---

### Attendance

- Create attendance session
- Mark attendance
- Edit attendance

---

### Assignments

- Create assignment
- Publish assignment
- View submissions
- Grade assignments

---

### Marks

- Enter marks
- Edit marks
- Submit marks

---

### Materials

- Upload lecture slides
- Upload notes
- Upload documents

---

### Hall Duty

Displays assigned examination duties.

---

## Permissions

Faculty can only manage courses assigned to them.

They cannot modify another faculty member's courses.

---

# 8. Accounts

## Purpose

Manages all student financial activities.

---

## Responsibilities

- Receive payments
- Generate receipts
- View payment history
- Apply waivers
- Monitor dues
- Verify payment clearance
- Student financial reports

---

## Dashboard Features

### Dashboard

Financial summary.

---

### Students

Filter students by

- Department
- Semester

Search by

- Student ID

---

### Student Payment Profile

Displays

- Student information
- Payment history
- Due history
- Fee structure
- Waivers
- Current balance
- Admit card eligibility

Actions

- Receive payment
- Print receipt
- Apply waiver
- View transaction history

---

### Payments

Shows

- Recent payments
- Payment search
- Payment reports

---

### Due Management

Shows

- Current dues
- Outstanding balances

---

### Waivers

Manage

- Financial waivers
- Scholarship adjustments

---

### Receipts

View and reprint receipts.

---

### Reports

Financial reporting

- Collection summary
- Due summary
- Semester reports

---

## Permissions

Cannot modify

- Marks
- Attendance
- Courses

---

# 9. Exam Controller

## Purpose

Responsible for the complete examination process.

---

## Responsibilities

- Create exam routines
- Edit exam routines
- Publish routines
- Assign hall duties
- Generate seat plans
- Publish results
- Manage admit cards

---

## Dashboard Features

### Dashboard

Overview

---

### Exam Routine

- Create
- Edit
- Delete
- Publish

---

### Seat Plans

Assign

- Room
- Seat Number

---

### Hall Duty

Assign faculty invigilators.

---

### Admit Cards

Publish

Generate

Monitor eligibility

---

### Results

Publish

Unpublish

---

## Permissions

Cannot edit marks.

Can only publish already submitted marks.

---

# 10. Student

## Purpose

Students access academic information through a self-service portal.

---

## Dashboard Modules

### Dashboard

Overview

---

### Profile

Personal information.

---

### Courses

Current semester courses.

---

### Attendance

Attendance percentage.

Course-wise attendance.

---

### Results

Published

Midterm

Final

CGPA

Semester GPA

---

### Payments

Payment history

Receipts

Due information

Waivers

---

### Exam Routine

Published examination schedule.

---

### Seat Plan

Exam room

Seat number

---

### Admit Card

Download PDF

Eligibility status

---

### Course Materials

Download uploaded materials.

---

### Assignments

Submit assignments.

Track submission status.

---

### Applications

Submit applications to

- Faculty
- Department Head
- Accounts
- Exam Controller
- Admin

Track application status.

---

## Permissions

Students can only access their own information.

No student can access another student's data.

---

# 11. Security Model

The portal enforces permissions at multiple layers.

### Login Required

Every protected page requires authentication.

---

### Role Validation

Each view verifies the user's role before granting access.

Example

```
if request.user.role != "accounts":
    return redirect("dashboard")
```

---

### Object Ownership

Even within the same role, users can only access records they own.

Examples

Faculty

Only their assigned Course Offerings.

Students

Only their own attendance, marks, payments, and applications.

---

### URL Protection

Direct URL access does not bypass permissions.

Unauthorized users are redirected.

---

# 12. Current Status

Implemented

✓ Role-based login

✓ Role-specific dashboards

✓ Permission checks

✓ Navigation separation

✓ Dedicated sidebar menus

✓ Student self-service

✓ Faculty workflow

✓ Accounts workflow

✓ Examination workflow

✓ Department-based access

---

# 13. Planned Enhancements

Future improvements include

- Fine-grained permission groups
- Temporary delegated access
- Audit logging
- Activity history
- Two-factor authentication
- Session monitoring
- API permission scopes
- Permission management interface

---

# 14. Design Philosophy

The permission system is designed to mirror how responsibilities are distributed within a real university.

Rather than granting broad access, each role is given only the tools necessary for its responsibilities. This reduces complexity, improves security, and creates a focused user experience.

As additional modules such as Library, Hostel, Payroll, HR, and Alumni are introduced, they will integrate with this same role-based architecture to maintain consistency across the portal.