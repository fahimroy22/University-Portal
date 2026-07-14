
# 🎓 Smart University Portal

**A full-stack University ERP system built with Django — digitizing the complete academic and administrative lifecycle of a modern university.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange)](docs/15_Project_Roadmap.md)

[Overview](#-overview) •
[Features](#-features) •
[Architecture](#-architecture) •
[Database Design](#-database-design) •
[Roles & Permissions](#-user-roles--permissions) •
[Getting Started](#-getting-started) •
[Documentation](#-documentation) •
[Roadmap](#-roadmap)

</div>

---

## 📖 Overview

**Smart University Portal** is an Enterprise Resource Planning (ERP) system being developed for the **University of Global Village (UGV)**. Rather than a simple student management tool, it aims to replicate how a real university actually operates — bringing academics, finance, examinations, faculty operations, student services, and administration into a single, connected platform.

The project follows a **modular monolith** architecture: every domain (students, faculty, finance, exams, etc.) lives in its own Django app with its own models, views, templates, and URLs, while sharing a common academic data backbone (`Department → Program → Batch → Semester → Course → Course Offering`).

| | |
|---|---|
| **Architecture** | Modular monolith (Django apps per domain) |
| **Rendering** | Server-side (Django Templates + Tailwind CSS) |
| **User Roles** | 7 role-based dashboards |
| **Django Apps** | 9 (`accounts`, `academics`, `students`, `faculty`, `exams`, `finance`, `notices`, `applications`, `dashboard`) |
| **Status** | Active development — roadmap in [`docs/15_Project_Roadmap.md`](docs/15_Project_Roadmap.md) |

---

## ✨ Features

<table>
<tr>
<td valign="top" width="50%">

### 🎓 Student Portal
- Personal dashboard & profile
- Course registration
- Current & previous semester courses
- Attendance tracking
- Assignment submission
- Marks, GPA & semester results
- Exam routine & seat plan
- Admit card download (PDF)
- Finance: payments, dues, waivers, receipts
- Applications to Faculty / Dept. Head / Accounts / Exam Controller
- Mark review requests

### 👨‍🏫 Faculty Portal
- Assigned course offerings
- Attendance sessions & records
- Assignment creation, review & grading
- Marks entry & submission
- Course material uploads
- Hall duty schedule
- Mark review verification
- Result correction request creation

</td>
<td valign="top" width="50%">

### 🏢 Department Head Portal
- Faculty & student monitoring
- Department-level academic overview
- Course enrollment monitoring
- Department reports

### 🏛️ Exam Controller Portal
- Exam routine creation & publishing
- Seat plan generation
- Hall duty assignment
- Admit card eligibility & publishing
- Result publishing & correction workflow
- Exam committee review

### 💰 Finance Module
- Program fee structures
- Student financial profiles
- Payments, receipts & waivers
- Due management & reports
- Bulk student upload

### ⚙️ Administration
- User & role management
- Academic setup (departments, batches, semesters, courses, offerings)
- System settings & notices
- Audit logs

</td>
</tr>
</table>

### 🔁 Signature Workflow — Result Correction

A concrete example of how the system models a real institutional process end-to-end:

```mermaid
flowchart LR
    A[Student<br/>submits Mark Review] --> B[Faculty<br/>verification]
    B --> C[Official Result<br/>Correction Request]
    C --> D[Exam Controller<br/>verification]
    D --> E[Super Admin<br/>approval]
    E --> F[Result<br/>updated & republished]
```

---

## 🏗 Architecture

```mermaid
flowchart TB
    Browser["🌐 Web Browser"]
    Router["Django URL Router"]

    subgraph Apps["Domain Applications"]
        direction LR
        Accounts["accounts<br/>(auth & roles)"]
        Academics["academics<br/>(dept · course · offering)"]
        Students["students"]
        Faculty["faculty"]
        Finance["finance"]
        Exams["exams"]
        Applications["applications"]
        Notices["notices"]
        Dashboard["dashboard<br/>(role UIs & routing)"]
    end

    Shared["Shared Models &<br/>Business Logic"]
    Auth["Django Authentication<br/>+ Role-Based Access Control"]
    DB[("Database<br/>SQLite (dev) / PostgreSQL (prod)")]
    PDF["ReportLab<br/>(admit cards · receipts · results)"]

    Browser --> Router --> Apps
    Apps --> Shared --> Auth --> DB
    Apps -.-> PDF
```

**Request flow** — every module follows the same, template-only path (no business logic in templates):

```mermaid
flowchart LR
    Browser --> URL --> View --> Logic["Business Logic"] --> Model --> DB[(Database)]
    DB --> Template --> Browser
```

### Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Django, Django ORM |
| **Frontend** | HTML5, Django Template Engine, Tailwind CSS, JavaScript |
| **Database** | SQLite (development) → PostgreSQL (planned for production) |
| **PDF Generation** | ReportLab — admit cards, payment receipts, result sheets |
| **Auth** | Django Authentication with a custom `User` model + role-based authorization |
| **Build tooling** | PostCSS, Autoprefixer, Tailwind CLI (`package.json`) |
| **Version control** | Git / GitHub |

---

## 🗄 Database Design

Every academic activity is anchored to the `CourseOffering` model — it's the connective tissue between courses, faculty, students, attendance, marks, and exams.

```mermaid
erDiagram
    DEPARTMENT ||--o{ PROGRAM : offers
    PROGRAM ||--o{ BATCH : admits
    BATCH ||--o{ COURSE_REGISTRATION : contains
    DEPARTMENT ||--o{ COURSE : owns
    SEMESTER ||--o{ COURSE : scheduled_in
    COURSE ||--o{ COURSE_OFFERING : "offered as"
    FACULTY ||--o{ COURSE_OFFERING : teaches
    STUDENT_PROFILE ||--o{ COURSE_REGISTRATION : enrolls
    COURSE_OFFERING ||--o{ COURSE_REGISTRATION : "registered via"
    COURSE_OFFERING ||--o{ ATTENDANCE_SESSION : has
    ATTENDANCE_SESSION ||--o{ ATTENDANCE_RECORD : logs
    COURSE_OFFERING ||--o{ ASSIGNMENT : has
    ASSIGNMENT ||--o{ ASSIGNMENT_SUBMISSION : receives
    STUDENT_PROFILE ||--o{ MARKS : earns
    COURSE_OFFERING ||--o{ MARKS : graded_in
    COURSE_OFFERING ||--o{ EXAM_ROUTINE : scheduled
    STUDENT_PROFILE ||--o{ ADMIT_CARD : issued
    STUDENT_PROFILE ||--o{ STUDENT_FEE : owes
    STUDENT_FEE ||--o{ PAYMENT : "settled by"
    PROGRAM_FEE_STRUCTURE ||--o{ STUDENT_FEE : defines
    USER ||--o| STUDENT_PROFILE : "is a"
    USER ||--o| FACULTY : "is a"
```

**Core academic hierarchy:**

```
Department → Program → Batch → Semester → Course → Course Offering → { Faculty, Students }
```

**Finance chain:** `Program Fee Structure → Student Financial Profile → Student Fee → Payment → Receipt`
**Examination chain:** `Exam Routine → Seat Plan → Hall Duty → Admit Card → Result Publication`

Students never link directly to a `Course` — they link through **Course Registration → Course Offering**, which is what allows multiple sections, retakes, and repeated semesters to coexist cleanly. Full model-by-model detail lives in [`docs/02_Database_Design.md`](docs/02_Database_Design.md).

---

## 👥 User Roles & Permissions

The portal is built around **Role-Based Access Control (RBAC)** — every user has exactly one role, and sees only the dashboard and data relevant to it.

```mermaid
flowchart TD
    SA["Super Admin<br/>full system access"]
    A["Admin<br/>day-to-day administration"]
    DH["Department Head<br/>department scope"]
    FA["Faculty<br/>assigned courses only"]
    AC["Accounts<br/>finance only"]
    EC["Exam Controller<br/>examinations only"]
    ST["Student<br/>own data only"]

    SA --> A
    A --> DH
    A --> AC
    A --> EC
    DH --> FA
    EC --> ST
```

| Role | Scope | Can't do |
|---|---|---|
| **Super Admin** | Full CRUD across every module, system configuration | — |
| **Admin** | Academic & student management, courses, batches, notices | System-level configuration |
| **Department Head** | Faculty/student monitoring & reports for their department | Modify other departments |
| **Faculty** | Attendance, assignments, marks, materials for *their own* course offerings | Touch another faculty member's courses |
| **Accounts** | Payments, receipts, waivers, dues, financial reports | Marks, attendance, courses |
| **Exam Controller** | Exam routine, seat plans, hall duty, admit cards, publish results | Edit submitted marks |
| **Student** | Self-service: courses, attendance, results, payments, applications | Access another student's data |

Permissions are enforced at multiple layers: `login_required` decorators, per-view role checks, object-ownership checks (e.g. a faculty member can only touch their own `CourseOffering`), and CSRF/ORM protection against injection. Full breakdown in [`docs/03_User_Roles.md`](docs/03_User_Roles.md).

---

## 📂 Project Structure

```
University-Portal/
├── accounts/          # Custom User model, authentication, roles
├── academics/         # Departments, programs, batches, semesters, courses, offerings
├── students/          # Student profiles, academic records
├── faculty/            # Faculty profiles, teaching assignments
├── exams/              # Exam routine, seat plans, hall duty, admit cards, results
├── finance/            # Fee structures, student fees, payments, waivers
├── notices/            # University-wide announcements
├── applications/       # Student → staff application workflow
├── dashboard/           # Role-based dashboards, view_modules/, shared URLs
│   └── view_modules/    # Views split by domain (academic, faculty, exam_controller, ...)
├── config/              # Django project settings, URLs, WSGI/ASGI
├── templates/            # Server-rendered HTML (base + per-role dashboards)
├── static/               # CSS, JS, images
├── docs/                  # 20+ living design & architecture documents
└── manage.py
```

**Scale at a glance:** 9 Django apps · ~19,000 lines of Python · 75 templates · 36 migrations.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip / virtualenv
- Node.js (only needed if you want to rebuild the Tailwind CSS bundle)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/fahimroy22/University-Portal.git
cd University-Portal

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install backend dependencies
pip install django reportlab

# 4. (Optional) Install frontend tooling for Tailwind CSS
npm install

# 5. Apply migrations
python manage.py migrate

# 6. Create a superuser (for the Super Admin dashboard)
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` and log in with the account you created (or a seeded role account, if you've loaded the mock institutional dataset described in [`docs/14_Test_Data.md`](docs/14_Test_Data.md)).

> **Note:** this repository doesn't yet ship a `requirements.txt` / `package-lock`-equivalent pin file for Python — the project currently only depends on **Django** and **ReportLab** beyond the standard library. Freezing these with `pip freeze > requirements.txt` once versions stabilize is tracked as a housekeeping item.

### Configuration notes
- `DEBUG = True` and the database is **SQLite** by default — both are development-only settings; switch to PostgreSQL and `DEBUG = False` with a real `SECRET_KEY` before any production deployment.
- The custom user model is `accounts.User` (`AUTH_USER_MODEL`), with `role` as its central RBAC field.

---

## 📚 Documentation

This project treats documentation as a first-class citizen — every module has a living design doc under [`docs/`](docs/):

| Doc | Covers |
|---|---|
| [00_Project_Overview](docs/00_Project_Overview.md) | Vision, objectives, scope |
| [01_System_Architecture](docs/01_System_Architecture.md) | Full software architecture |
| [02_Database_Design](docs/02_Database_Design.md) | Models & relationships |
| [03_User_Roles](docs/03_User_Roles.md) | Role permissions |
| [04_UI_Guidelines](docs/04_UI_Guidelines.md) | Design language |
| [05–13] | Per-portal deep dives (Admin, Academic Setup, User Mgmt, Finance, Student, Faculty, Dept. Head, Exam Controller, Results) |
| [14_Test_Data](docs/14_Test_Data.md) | Mock institutional dataset |
| [15_Project_Roadmap](docs/15_Project_Roadmap.md) | Phased future plans |
| [16_Deployment_and_Operations](docs/16_Deployment_and_Operations.md) | Deployment guide |
| [17_API_and_URL_Reference](docs/17_API_and_URL_Reference.md) | URL map & future REST API |
| [18_Management_Commands](docs/18_Management_Commands.md) | Django management commands |
| [19_Known_Issues](docs/19_Known_Issues.md) | Bugs & pending fixes |
| [20_Development_Workflow](docs/20_Development_Workflow.md) | Contribution conventions |

---

## 🗺 Roadmap

Estimated overall completion: **~70%**

- [x] Project structure, authentication, RBAC
- [x] Academic setup, student registration, faculty assignment
- [x] Finance infrastructure (fees, payments, waivers, receipts)
- [x] Examination infrastructure (routine, seat plan, admit cards)
- [ ] Attendance system *(open)*
- [ ] Result generation & transcripts *(open)*
- [ ] Payment gateway integration
- [ ] REST API layer (for a planned mobile app)
- [ ] Notification center & email service
- [ ] Dark mode, analytics, audit log viewer

Long-term vision includes an Android app, AI academic advisor, LMS integration, library & hostel management, and an alumni portal. Full detail in [`docs/15_Project_Roadmap.md`](docs/15_Project_Roadmap.md).

---

## 🖼 Screenshots

<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/fc991b1a-86f8-4d85-8200-35b9d1e445ca" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/75e9b7ea-8e59-4e97-9ad6-3c15e5005023" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/23ff8d55-387b-4863-bd12-99f08bdc5801" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/0a63bf8e-05e1-413d-8e1d-65256378a803" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/4b5a9e71-4184-43f0-9516-a3e90cfc36c0" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/5c15168f-eaa6-4b2c-938d-fb6814d6bfd2" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/d8a76c86-89d1-4e00-a054-2f59c0b7dcdd" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/b50116e1-a3f2-48f5-b9d1-67575a7c8390" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/572244d5-ed0e-44a4-9a8b-0c6dc7962086" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/c6794dc0-e4c7-4331-8266-680c7dbb1d41" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/1b080922-b2c1-4dee-81a4-44b8f31be266" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/47ed1210-60c4-4f1d-9e91-f98c226cc16d" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/9e3d6ff5-3df5-4230-a7ae-451acbf20630" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/c00a8e5a-9df2-407b-b0d9-7a609a6de81c" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/e6e99f13-1fab-44c7-aef0-254ff258e4dd" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/89c12e22-a4bb-4744-82d7-5d9c45672a1a" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/4ca6e8f0-b8dd-48db-8140-3050066c03bd" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/a201de44-1f15-4c97-900d-2661d1c49044" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/ad58fee6-a514-4458-8865-7b2bcb9911c0" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/8de24ce8-f8d3-4f72-9a6e-4bd7f84a1c60" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/e1355e2a-c267-4107-b190-c833b2358a02" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/2c8cae27-0b0a-404d-b721-6465dabbc07a" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/7ada50b4-cb6b-4fa1-8340-f33c052cbaf2" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/d405f803-6a55-4752-ba06-73ea6db8b096" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/b7a9f0fa-6866-4f3d-8ca8-f640c79b8a92" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/a81a1edd-64fd-4768-9b55-b36155c9aec4" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/8afe6a52-2fab-4ffa-88b4-de5e6dd7e841" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/76daad79-da3d-41db-98ef-f12b044418f6" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/7bc81a5c-d9b1-4cbf-887a-a1318b6e5e6e" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/45795488-34c7-4965-8f08-4b7e05476088" />
<img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/2f2394c9-9c26-4d51-9fa7-8670b227c827" />



















---

## 🤝 Contributing

Contributions should follow the conventions in [`docs/20_Development_Workflow.md`](docs/20_Development_Workflow.md) and [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — keep workflows realistic, update the relevant `docs/` file alongside any code change, and log major changes in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## 👤 Author

**Fahim Ahmed**
B.Sc. in Computer Science & Engineering — University of Global Village
Full-Stack Developer

## 📄 License

Licensed under the [MIT License](LICENSE).
