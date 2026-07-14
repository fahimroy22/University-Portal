# API and URL Reference

> Version: 1.0

---

# Overview

This document lists all major URLs, views, and future API endpoints used by the UGV Smart University Portal.

Current architecture is server-side rendered using Django Templates.

Future versions may expose REST APIs for the Android application.

---

# Authentication

Login

/login/

Logout

/logout/

Password Change

/password-change/

---

# Admin Portal

Dashboard

/admin/

Academic Setup

/academic-setup/

User Management

/super-admin/users/

Bulk Student Upload

/super-admin/bulk-student-upload/

Audit Logs

/audit/

System Settings

/settings/

---

# Academic Setup

Departments

/academic-setup/departments/

Programs

/academic-setup/programs/

Batches

/academic-setup/batches/

Semesters

/academic-setup/semesters/

Courses

/academic-setup/courses/

Course Offerings

/academic-setup/course-offerings/

---

# Student Portal

Dashboard

/student/

Profile

/student/profile/

Course Registration

/student/course-registration/

Results

/student/results/

Finance

/student/finance/

Routine

/student/routine/

Attendance

/student/attendance/

---

# Faculty Portal

Dashboard

/faculty/

Attendance

/faculty/attendance/

Marks

/faculty/marks/

Assignments

/faculty/assignments/

Students

/faculty/students/

---

# Accounts Portal

Overview

/accounts/

Student Accounts

/accounts/students/

Dues

/accounts/dues/

Payments

/accounts/payments/

Waivers

/accounts/waivers/

Receipts

/accounts/receipts/

Admit Cards

/accounts/admit-cards/

Reports

/accounts/reports/

Student Detail

/accounts/student/<student_id>/

---

# Department Head

/dashboard/head/

Faculty

/dashboard/head/faculty/

Results

/dashboard/head/results/

Reports

/dashboard/head/reports/

---

# Exam Controller

/exam/

Routine

/exam/routine/

Seat Plan

/exam/seat-plan/

Publish Results

/exam/results/

Transcript

/exam/transcript/

---

# Future REST API

/api/login/

/api/student/

/api/payment/

/api/results/

/api/attendance/

/api/notifications/

/api/course-registration/

---

# Naming Convention

Views

snake_case

Models

PascalCase

Templates

snake_case

URLs

kebab-case

Context Variables

snake_case

---

# URL Design Rules

Every module owns its own URLs.

Example

/accounts/*

Student Portal never directly accesses Admin URLs.

All permissions are enforced at the view level.