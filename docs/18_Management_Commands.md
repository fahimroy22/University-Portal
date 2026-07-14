# Management Commands

> Version: 1.0

---

# Overview

This document records useful management commands for development, testing, database initialization, and mock data generation.

---

# Run Server

python manage.py runserver

---

# Make Migrations

python manage.py makemigrations

---

# Apply Migrations

python manage.py migrate

---

# Create Superuser

python manage.py createsuperuser

---

# Collect Static Files

python manage.py collectstatic

---

# Shell

python manage.py shell

---

# Reset Database

python manage.py flush

---

# Academic Data Commands

Create Departments

python manage.py seed_departments

Create Programs

python manage.py seed_programs

Create Batches

python manage.py seed_batches

Create Semesters

python manage.py seed_semesters

Create Courses

python manage.py seed_courses

Create Course Offerings

python manage.py seed_course_offerings

---

# User Commands

Create Faculty

python manage.py seed_faculty

Bulk Student Upload

Admin Portal CSV Upload

Create Accounts Users

python manage.py seed_accounts

Create Exam Controller

python manage.py seed_exam_controller

---

# Finance Commands

Generate Finance Records

python manage.py seed_finance

Generate Payment History

python manage.py seed_payment_history

Generate Mock Receipts

python manage.py seed_receipts

Generate Waivers

python manage.py seed_waivers

---

# Testing Commands

Generate Mock Results

python manage.py seed_results

Generate Attendance

python manage.py seed_attendance

Generate Course Registration

python manage.py seed_registration

---

# Useful Django Commands

Show Migrations

python manage.py showmigrations

SQL Migration

python manage.py sqlmigrate app 0001

Check Project

python manage.py check

---

# Future Commands

Backup Database

Restore Database

Generate Transcript PDFs

Generate Admit Cards