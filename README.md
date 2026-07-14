# 🎓 Smart University Portal

A modern, full-stack University ERP (Enterprise Resource Planning) system built with **Django**, designed to digitalize every major academic and administrative workflow of a university.

Developed as a production-style project with multiple role-based dashboards, workflow automation, and modern UI/UX.

---

## ✨ Features

### 👨‍🎓 Student Portal

- Student Dashboard
- Course Registration
- Current & Previous Semester Courses
- Attendance Tracking
- Assignment Submission
- Marks & GPA
- Semester Results
- Seat Plan
- Admit Card
- Notices
- Finance & Payments
- Waiver Information
- Applications
- Hall Information
- Student Profile
- Academic Summary
- Mark Review Requests

---

### 👨‍🏫 Faculty Portal

- Faculty Dashboard
- Course Management
- Student List
- Attendance Management
- Assignment Review
- Marks Management
- Reports
- Applications
- Hall Duties
- Mark Review Verification
- Result Correction Request Creation

---

### 🏢 Department Head Portal

- Faculty Monitoring
- Student Monitoring
- Academic Overview
- Reports
- Course Enrollment Monitoring

---

### 🏛️ Exam Controller Portal

- Result Management
- Result Correction Workflow
- Faculty Verification
- Exam Committee Review
- Seat Plan Generation
- Admit Card Management
- Audit Logs

---

### 💰 Finance Module

- Program Fee Structure
- Student Fees
- Payment Tracking
- Waivers
- Receipts
- Financial Profile
- Bulk Student Upload
- Finance Dashboard

---

### ⚙️ Administration

- User Management
- Role Management
- System Settings
- Audit Logs
- Notice Management
- Dashboard Analytics

---

## ⭐ Major Workflow

### Student Result Review Workflow

Student

↓

Creates Mark Review Request

↓

Faculty Verification

↓

Official Result Correction Request

↓

Exam Controller Verification

↓

Super Admin Approval

↓

Official Result Updated

---

## 🏗 Architecture

```
Django
│
├── Authentication
├── Student Module
├── Faculty Module
├── Finance Module
├── Examination Module
├── Applications
├── Notices
├── Dashboard
├── Audit Logs
└── Administration
```

---

## 🖥 Technology Stack

### Backend

- Django
- Python
- SQLite (Development)

### Frontend

- HTML5
- CSS3
- Tailwind CSS
- JavaScript

### Database

- SQLite
- Easily configurable for PostgreSQL/MySQL

### Version Control

- Git
- GitHub

---

## Design Philosophy

This project follows a modern dashboard design inspired by enterprise software.

Goals include:

- Clean UI
- Consistent component system
- Professional typography
- Responsive layouts
- Workflow-driven design
- Role-based dashboards

---

## Project Structure

```
accounts/
academics/
applications/
dashboard/
finance/
faculty/
students/
notices/
templates/
static/
config/
manage.py
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/fahimryo22/University-Portal.git
```

Go inside

```bash
cd University-Portal
```

Create virtual environment

```bash
python -m venv venv
```

Activate

macOS/Linux

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations

```bash
python manage.py migrate
```

Run server

```bash
python manage.py runserver
```

---

## Current Status

🚧 Active Development

Major modules completed:

- Student Portal
- Faculty Portal
- Finance Module
- Examination Module
- Result Correction Workflow
- Mark Review Workflow

Upcoming:

- Email Notifications
- API Layer
- Advanced Analytics
- Mobile Responsive Improvements
- Production Deployment

---

## Screenshots

*(Add screenshots here as the project grows.)*

---

## Future Roadmap

- REST API
- Mobile App
- QR Attendance
- AI Assistant
- Notification Center
- LMS Integration
- Online Examination
- Payment Gateway

---

## Author

**Fahim Ahmed**

B.Sc. in Computer Science & Engineering

University of Global Village

Full Stack Developer

---

## License

This project is licensed under the MIT License.