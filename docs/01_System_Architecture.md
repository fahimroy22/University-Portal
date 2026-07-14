# System Architecture

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The UGV Smart University Portal follows a modular monolithic architecture built using Django.

Instead of developing one massive application, the project is divided into multiple independent Django applications, each responsible for one business domain.

Although deployed as a single system, every module has a clearly defined responsibility.

This approach provides:

- Easier maintenance
- Better scalability
- Cleaner code organization
- Faster feature development
- Simpler debugging

---

# 2. High Level Architecture

```

                        +-----------------------+
                        |      Web Browser      |
                        +-----------+-----------+
                                    |
                                    |
                           Django URL Router
                                    |
          ---------------------------------------------------
          |        |         |        |        |             |
          |        |         |        |        |             |
      Accounts  Students  Faculty  Academics Finance Exams
          |        |         |        |        |             |
          ---------------------------------------------------
                           Shared Models
                                  |
                           Authentication
                                  |
                           PostgreSQL Database

```

---

# 3. Technology Stack

## Backend

- Python
- Django
- Django ORM

---

## Frontend

- HTML5
- CSS3
- Tailwind CSS
- JavaScript
- Django Template Engine

---

## Database

- PostgreSQL

(Currently SQLite may be used during development.)

---

## PDF Generation

- ReportLab

Used for

- Admit Cards
- Payment Receipts
- Result Sheets

---

## Authentication

- Django Authentication
- Custom User Model
- Role-Based Authorization

---

# 4. Application Structure

The project is divided into independent Django applications.

```

UGV Portal

accounts/
students/
faculty/
academics/
finance/
exams/
applications/
dashboard/
notices/
core/

```

Each application owns its own:

- models
- views
- templates
- urls
- business logic

---

# 5. User Roles

The portal currently supports seven user roles.

## Super Admin

Full system access.

Responsibilities

- Configure portal
- Manage all users
- System maintenance

---

## Admin

Administrative management.

Responsibilities

- User management
- Academic management
- Student management

---

## Department Head

Department-specific administration.

Responsibilities

- Faculty supervision
- Course approvals
- Department reports

---

## Faculty

Responsible for teaching.

Responsibilities

- Attendance
- Assignments
- Marks
- Course materials
- Hall duties

---

## Accounts

Responsible for finance.

Responsibilities

- Student payments
- Waivers
- Receipts
- Dues
- Reports

---

## Exam Controller

Responsible for examination management.

Responsibilities

- Exam routines
- Seat plans
- Hall duties
- Admit cards
- Result publication

---

## Student

Student self-service portal.

Responsibilities

- View courses
- Attendance
- Results
- Payments
- Applications
- Materials
- Exam routine
- Seat plan
- Admit card

---

# 6. Data Flow

Most workflows follow the same architecture.

```

Browser

↓

URL

↓

View

↓

Business Logic

↓

Model

↓

Database

↓

Template

↓

Browser

```

No business logic should exist inside templates.

Views remain lightweight whenever possible.

Complex calculations are extracted into helper functions.

---

# 7. Shared Data Model

Although applications are independent, they are connected through shared models.

Example relationships

```

Department

↓

Program

↓

Batch

↓

Semester

↓

Course

↓

Course Offering

↓

Faculty
Student

↓

Attendance

↓

Marks

↓

Results

```

The Course Offering model acts as one of the central connecting entities.

---

# 8. Core Business Entities

Some models are referenced throughout the system.

Examples include

- User
- StudentProfile
- Department
- Semester
- Batch
- Course
- CourseOffering

These serve as foundational models upon which other modules depend.

---

# 9. Dashboard Architecture

Each role has an independent dashboard.

Example

```

Dashboard

├── Student Dashboard

├── Faculty Dashboard

├── Accounts Dashboard

├── Exam Controller Dashboard

├── Department Head Dashboard

├── Admin Dashboard

└── Super Admin Dashboard

```

This separation keeps workflows organized and reduces interface complexity.

---

# 10. Design Principles

The architecture follows several design principles.

### Separation of Concerns

Each module performs one responsibility.

---

### Reusability

Business logic should be reusable.

Common calculations are implemented once and reused throughout the project.

---

### Maintainability

Files remain organized by responsibility.

Large modules are gradually refactored into smaller components when necessary.

---

### Scalability

Future modules can be added without redesigning the existing architecture.

Examples

- Library
- Hostel
- Payroll
- LMS
- Alumni

---

### Consistency

Every page follows consistent

- styling
- navigation
- permissions
- dashboard layouts
- responsive behavior

---

# 11. Security

Security measures include

- Login required decorators
- Role checking
- Object ownership validation
- CSRF protection
- Django ORM protection against SQL injection
- File upload validation
- Permission-based navigation

Future improvements include

- Audit logs
- Two-factor authentication
- Login history
- API authentication

---

# 12. Current Architecture Status

Completed

✓ Modular project structure

✓ Authentication

✓ Role management

✓ Academic module

✓ Student module

✓ Faculty module

✓ Finance module

✓ Examination module

✓ Responsive dashboards

✓ PDF generation

✓ Mock institutional dataset

In Progress

- Documentation
- Reports
- Dashboard refinements
- Accounts improvements

Future

- Notification center
- LMS
- Library
- HR
- Hostel
- Payroll
- Analytics

---

# 13. Architectural Goals

The architecture is designed so that every university operation flows naturally through a connected system rather than isolated applications.

The long-term objective is to maintain a clean, scalable, production-ready ERP capable of supporting the complete academic lifecycle of the University of Global Village.