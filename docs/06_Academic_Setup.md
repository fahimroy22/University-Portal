# Academic Setup Module

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The Academic Setup module is the foundation of the entire UGV Smart University Portal.

Almost every other module—including Student Management, Faculty, Examination, Finance, Results, Attendance, and Course Registration—depends on the academic structure defined here.

This module is typically configured once before each academic year and updated whenever the university introduces new programs, departments, courses, or semesters.

---

# 2. Purpose

The Academic Setup module is responsible for defining the university's academic structure.

It manages:

- Departments
- Batches
- Semesters
- Courses
- Course Offerings

Together these entities form the backbone of the ERP.

---

# 3. Current Status

Development Status

🟢 Mostly Complete

Completed

✓ Department Management

✓ Batch Management

✓ Semester Management

✓ Course Management

✓ Course Offering Management

✓ Statistics Dashboard

✓ Edit & Delete Operations

✓ Faculty Assignment

Remaining

- Automatic course offering generation
- Academic calendar integration
- Curriculum versioning
- Elective management
- Semester rollover automation

---

# 4. Academic Hierarchy

The system follows the following hierarchy.

```
University
│
├── Department
│
├── Batch
│
├── Semester
│
├── Course
│
└── Course Offering
```

Everything eventually points to a Course Offering.

---

# 5. Dashboard

The Academic Setup dashboard provides an overview of the academic structure.

Current dashboard statistics include:

- Total Departments
- Total Batches
- Total Semesters
- Total Courses
- Total Course Offerings

These values update automatically.

---

# 6. Departments

Departments represent the highest academic unit.

Current Departments

| Code | Department |
|------|------------|
|001|Computer Science & Engineering|
|002|Civil Engineering|
|003|Electrical & Electronic Engineering|
|004|Mechanical Engineering|
|005|Business Administration|
|006|English|
|007|Law|
|008|Cyber Security|

Each department contains its own

- Faculty
- Students
- Courses
- Batches
- Course Offerings

---

# 7. Batch Management

A batch represents an admission session.

Example

```
001 - Winter - 2023
```

Current implementation supports

- Department
- Batch Name
- Admission Year

---

## Academic Timeline

The current testing environment uses the following timeline.

| Batch | Current Semester |
|--------|-----------------|
|Winter 2023|8th Semester|
|Summer 2023|7th Semester|
|Winter 2024|6th Semester|
|Summer 2024|5th Semester|
|Winter 2025|4th Semester|
|Summer 2025|3rd Semester|
|Winter 2026|2nd Semester|
|Summer 2026|1st Semester|

As time progresses

New batches will be added.

Older batches will graduate.

---

# 8. Semester Management

The system currently supports eight semesters.

```
1st Semester

↓

2nd Semester

↓

3rd Semester

↓

4th Semester

↓

5th Semester

↓

6th Semester

↓

7th Semester

↓

8th Semester
```

Each course belongs to one semester.

---

# 9. Course Management

Courses define the curriculum.

Each course contains

- Course Code
- Course Title
- Credits
- Department
- Semester

Example

```
CSE 1101

Structured Programming

3 Credits

Semester 1
```

Current dataset contains approximately

140 courses.

---

# 10. Course Offerings

Course Offering is the most important entity in the academic module.

Instead of assigning students directly to a Course, students register into a Course Offering.

A Course Offering connects

```
Course

↓

Faculty

↓

Batch

↓

Semester

↓

Section
```

---

## Example

```
CSE 1101

Faculty

↓

Faculty 1

↓

Batch

001 - Summer - 2026

↓

Semester

1st Semester

↓

Section A
```

---

# 11. Sections

The system currently supports

Section A

Section B

Each Course Offering belongs to exactly one section.

Future

Dynamic section creation.

---

# 12. Faculty Assignment

Every Course Offering has

- Assigned Faculty
- Assigned Section
- Assigned Batch

Multiple sections may be assigned to different faculty.

Example

```
Section A

Faculty 1

Section B

Faculty 2
```

---

# 13. Course Offering Workflow

```
Create Course

↓

Create Batch

↓

Create Semester

↓

Assign Faculty

↓

Create Course Offering

↓

Students Register

↓

Faculty Takes Attendance

↓

Faculty Uploads Marks

↓

Results Published
```

---

# 14. Relationships

```
Department

↓

Batch

↓

Students

↓

Course Offerings

↓

Faculty

↓

Attendance

↓

Results
```

---

# 15. Testing Dataset

A realistic testing environment has been created.

Includes

- 8 Departments
- 81 Batches
- 8 Semesters
- ~140 Courses
- Faculty Members
- Course Offerings
- Student Dataset

This allows complete workflow testing.

---

# 16. Faculty Distribution

Each department has

Two faculty members

used for

Section A

Section B

Course distribution.

CSE already contains additional faculty used during testing.

---

# 17. Student Registration Logic

Students are **not** assigned directly to courses.

Instead

```
Student

↓

Course Registration

↓

Course Offering

↓

Faculty

↓

Attendance

↓

Marks

↓

Result
```

This design makes the system flexible for

- Multiple sections
- Retakes
- Faculty changes
- Batch-specific offerings

---

# 18. Current Mock Data

The testing environment includes

Departments

✓

Batches

✓

Faculty

✓

Courses

✓

Course Offerings

✓

Students

✓

Course Registrations

✓

This enables complete end-to-end testing.

---

# 19. Future Improvements

Planned enhancements include

- Automatic Course Offering generation
- Curriculum templates
- Elective management
- Course prerequisites
- Curriculum versioning
- Cross-department electives
- Summer improvement semesters
- Academic Calendar integration
- Semester rollover automation

---

# 20. Database Models

Primary models used

- Department
- Batch
- Semester
- Course
- CourseOffering

Related models

- StudentProfile
- FacultyProfile
- Enrollment
- Attendance
- Marks
- Results

---

# 21. URL Structure

Current pages

```
Academic Setup Dashboard

Departments

Batches

Semesters

Courses

Course Offerings
```

Each page supports

- Create
- Edit
- Delete

where permitted.

---

# 22. Permissions

Only

- Super Admin
- Admin

can modify academic structures.

Faculty and Students have read-only access to relevant academic information.

---

# 23. Design Decisions

Several important architectural decisions were made during development.

### Course Offering as the Central Entity

Instead of attaching students directly to courses, all registrations reference a Course Offering.

This allows

- Multiple faculty
- Multiple sections
- Semester-specific offerings
- Historical course records
- Future curriculum changes

without affecting student records.

### Batch Timeline

The testing dataset simulates a real university timeline by aligning batches with their current semesters rather than keeping all batches in the same semester.

### Realistic Testing Environment

Departments, batches, faculty, courses, course offerings, and students were populated with realistic mock data to allow complete workflow testing across Finance, Examination, Attendance, Results, and Student portals.

---

# 24. Long-Term Vision

The Academic Setup module is intended to become the single source of truth for all academic information within the ERP.

Every academic workflow—including admissions, registrations, attendance, examinations, results, finance, and graduation—will ultimately rely on the structures defined here.

Future development will focus on automating repetitive academic tasks while preserving the flexibility required for real-world university operations.