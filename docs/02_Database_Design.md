# Database Design

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The UGV Smart University Portal uses a relational database designed around the complete lifecycle of a university.

Rather than storing isolated pieces of information, every module is connected through carefully designed relationships.

The database is normalized to minimize duplication while maintaining fast access to frequently used information.

---

# 2. Core Entity Relationship

The overall academic hierarchy follows this structure.

```

University

↓

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
Students

↓

Attendance
Assignments
Materials
Marks
Exams

↓

Results

```

Everything revolves around the **Course Offering** model.

---

# 3. Main Applications

The database is divided into separate logical modules.

| Module | Purpose |
|---------|----------|
| Accounts | User authentication |
| Students | Student information |
| Academics | Departments, batches, semesters, courses |
| Faculty | Teaching, attendance, assignments, marks |
| Finance | Fees, payments, waivers |
| Exams | Routine, admit cards, seat plans |
| Applications | Student applications |
| Dashboard | UI and role dashboards |
| Notices | University announcements |

---

# 4. Authentication

## User

Every person inside the portal has exactly one User account.

Stores

- Username
- Password
- Email
- Name
- Role
- Active status

Supported roles

- Super Admin
- Admin
- Department Head
- Faculty
- Accounts
- Exam Controller
- Student

Relationships

```

User

├── StudentProfile

├── Faculty

├── Accounts

└── Admin

```

---

# 5. Academic Structure

## Department

Examples

- CSE
- EEE
- Civil
- English
- Law
- Pharmacy
- BBA

One department contains

- Courses
- Faculty
- Students

---

## Semester

Represents

1st through 8th semester.

Stores

- Semester name
- Order

---

## Batch

Represents student admission sessions.

Examples

Winter 2023

Summer 2023

Winter 2024

...

Each batch belongs to one department.

Each batch also has one current semester.

Current testing timeline

| Batch | Semester |
|---------|-----------|
| Winter 2023 | 8th |
| Summer 2023 | 7th |
| Winter 2024 | 6th |
| Summer 2024 | 5th |
| Winter 2025 | 4th |
| Summer 2025 | 3rd |
| Winter 2026 | 2nd |
| Summer 2026 | 1st |

---

# 6. Course

Each department owns its own curriculum.

A course stores

- Course Code
- Title
- Credit
- Department
- Semester

Example

CSE101

Programming Fundamentals

3 Credits

Semester 1

---

# 7. Faculty

Faculty members belong to departments.

Stores

- Employee ID
- User
- Department
- Designation

Faculty teach through Course Offerings.

---

# 8. Student Profile

StudentProfile extends the User model.

Stores

- Student ID
- Department
- Batch
- Current Semester
- Section
- Phone
- Address
- Guardian
- Photo

Student IDs follow a structured format.

Example

```
11012301
```

Meaning

```
11 = Department

01 = Batch

23 = Session

01 = Student Number
```

(Testing format may evolve later.)

---

# 9. Course Offering

Course Offering is the central model of the system.

Every running course creates one offering.

Stores

- Course
- Faculty
- Semester
- Batch
- Section
- Academic Year

Example

Programming

Semester 4

Batch Winter 2025

Section A

Faculty 01

Every other module references Course Offering.

---

# 10. Course Registration

Students never connect directly to Courses.

They connect through Course Registration.

Relationship

```

Student

↓

Course Registration

↓

Course Offering

```

This allows

- Multiple sections
- Retake courses
- Repeat semesters

---

# 11. Attendance

Attendance consists of two models.

Attendance Session

Represents one lecture.

Stores

- Course Offering
- Date

Attendance Record

Stores

- Student
- Session
- Present/Absent

Attendance percentage is calculated dynamically.

---

# 12. Assignments

Assignment

Stores

- Title
- Description
- Deadline
- Course Offering

Assignment Submission

Stores

- Student
- File
- Submission Time
- Status

---

# 13. Marks

Marks belong to

Student + Course Offering

Stores

- Class Test
- Assignment
- Attendance
- Midterm
- Final

Automatically calculates

- Total
- Grade
- Grade Point

Published only after approval.

---

# 14. Finance

Finance tracks the complete payment history.

Models

Program Fee Structure

↓

Student Financial Profile

↓

Student Fee

↓

Payments

↓

Waivers

Relationships

```

Student

↓

Financial Profile

↓

Student Fees

↓

Payments

↓

Receipts

```

---

# 15. Student Fee

Stores

- Fee Type
- Semester
- Amount
- Original Amount
- Waiver Amount
- Paid Amount

Current status

- Paid
- Partial
- Due

---

# 16. Payment

Every payment creates

- Receipt
- History
- Accounts record

Stores

- Amount
- Date
- Receiver
- Note

---

# 17. Waiver

Stores

- Student
- Amount
- Reason

Supports

- Manual waiver
- Fee waiver

---

# 18. Examination

Exam module contains

Exam Routine

↓

Seat Plan

↓

Hall Duty

↓

Admit Card

↓

Result Publication

---

# 19. Exam Routine

Stores

- Course Offering
- Exam Type
- Date
- Time
- Room

---

# 20. Seat Plan

Stores

- Student
- Course Offering
- Room
- Seat Number

---

# 21. Hall Duty

Stores

- Faculty
- Exam
- Duty Room
- Notes

---

# 22. Admit Card

Generated dynamically.

Eligibility depends on

- Attendance
- Payment clearance

---

# 23. Result Publication

Controls

Midterm

Final

Publication status

Results remain hidden until published.

---

# 24. Student Applications

Students can submit applications to

- Faculty
- Department Head
- Accounts
- Exam Controller
- Admin

Stores

- Subject
- Message
- Status

---

# 25. Notices

Stores

- Title
- Description
- Target audience
- Publish date

Displayed dynamically on dashboards.

---

# 26. Current Mock Dataset

The project currently includes a complete institutional testing dataset.

Includes

✓ Departments

✓ Semesters

✓ Courses

✓ Faculty

✓ Batches

✓ Sections

✓ Course Offerings

✓ Students

Testing data spans

Winter 2023

↓

Summer 2026

with proper semester progression.

Each course contains

Section A

Section B

Faculty assignments distributed across departments.

---

# 27. Planned Database Improvements

Future additions include

- Library
- Hostel
- Payroll
- Transport
- Alumni
- HR
- Research Management
- Inventory
- Scholarship
- Hostel Seat Allocation
- Course Prerequisites
- Multiple Advisors
- GPA History
- Audit Logs

---

# 28. Design Philosophy

The database has been designed around real university workflows rather than isolated software modules.

Every major activity—admission, registration, teaching, finance, examination, and graduation—flows naturally through connected entities.

This design minimizes redundancy while allowing the portal to scale as additional university services are introduced.