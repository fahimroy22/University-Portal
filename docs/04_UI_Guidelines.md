# UI & Design Guidelines

> Version: 1.0
>
> Last Updated: July 2026

---

# 1. Overview

The UGV Smart University Portal follows a modern, clean, and responsive design philosophy.

The objective is to create an interface that feels like a modern SaaS application while remaining simple enough for students, faculty, and university staff to use with minimal training.

The interface prioritizes:

- Simplicity
- Readability
- Consistency
- Accessibility
- Responsiveness
- Fast navigation

Rather than designing each page independently, every page follows the same design language.

---

# 2. Design Philosophy

Every page should answer three questions immediately.

1. Where am I?
2. What information is important?
3. What actions can I perform?

Users should never have to search for basic actions.

---

# 3. Overall Layout

Every dashboard follows the same structure.

```

+------------------------------------------------------+
| Sidebar | Top Header                                 |
|         |--------------------------------------------|
|         |                                            |
|         |                                            |
|         | Main Content                               |
|         |                                            |
|         |                                            |
|         |                                            |
+------------------------------------------------------+

```

---

# 4. Sidebar

The sidebar is the primary navigation component.

Design goals

- Fixed position
- Collapsible
- Icons for every menu
- Clear active page indicator
- Logical grouping

Sidebar should never cause pages to stretch horizontally.

---

# 5. Content Width

Pages should never occupy the full browser width.

Recommended wrapper

```html
<div class="max-w-7xl mx-auto">
```

This creates a cleaner reading experience.

---

# 6. Page Header

Every page begins with a consistent hero section.

Contains

- Badge
- Title
- Description
- Primary actions

Example

```
--------------------------------------------

[ Academic Module ]

Student Management

Manage student records, registration,
payments and academic history.

             + Add Student

--------------------------------------------
```

---

# 7. Summary Cards

Every dashboard begins with summary cards.

Cards display

- Totals
- Quick statistics
- Important indicators

Example

```
Students

245

Registered students

```

Avoid overcrowding.

Maximum

4–6 cards per row.

---

# 8. Page Organization

Large dashboards should be divided into dedicated pages.

Example

Instead of

Accounts Dashboard

with

- Payments
- Waivers
- Dues
- Reports
- Receipts
- Students

Split into

```
Accounts Dashboard

Students

Payments

Waivers

Receipts

Reports

Dues

```

This significantly improves usability.

---

# 9. Tables

Tables should only display essential information.

Never place excessive actions inside tables.

Recommended columns

✓ Name

✓ ID

✓ Status

✓ Date

✓ Actions

---

Large tables should use

```css
overflow-x-auto
```

instead of stretching the page.

---

# 10. Cards

Cards should be used for

Dashboard

Statistics

Student Profiles

Faculty Profiles

Payment summaries

Quick actions

Cards should have

- rounded corners
- subtle shadow
- consistent spacing

---

# 11. Buttons

Buttons follow three categories.

Primary

```
Maroon
```

Used for

Create

Save

Submit

Publish

---

Secondary

```
White
Border
```

Used for

Back

Cancel

View

---

Danger

```
Red
```

Used for

Delete

Reject

Remove

---

Buttons should have

- rounded corners
- hover animation
- consistent height

---

# 12. Forms

Forms should follow consistent spacing.

Each field contains

Label

↓

Input

↓

Validation message

Use grids for larger forms.

Example

```
Name

Department

Semester

Section

Batch

```

instead of long vertical layouts.

---

# 13. Filters

List pages should always provide filters.

Examples

Students

Department

Semester

Batch

Section

Status

---

Faculty

Department

Designation

---

Payments

Department

Semester

Status

---

Exam Routine

Department

Semester

Section

Exam Type

---

Filters should always appear above the table.

---

# 14. Search

Search should always remain visible.

Examples

Student ID

Employee ID

Course Code

Receipt Number

Application Number

Searching should navigate directly to the relevant record whenever possible.

---

# 15. Student Profile Pages

Student pages should act as a complete profile rather than scattered pages.

One profile should display

Student Information

↓

Academic Information

↓

Payments

↓

Attendance

↓

Results

↓

Applications

↓

Actions

This philosophy was adopted for the Accounts module.

---

# 16. Empty States

Every page should have an informative empty state.

Example

```
No payments found.

Payments will appear here after
transactions are recorded.

```

Avoid blank tables.

---

# 17. Badges

Use badges to display status.

Examples

Published

Pending

Paid

Partial

Due

Approved

Rejected

Completed

Active

Inactive

Badges should use consistent colors throughout the system.

---

# 18. Color Palette

Primary

Maroon

```
#7F1D1D
```

Primary Light

```
#FFF1F2
```

Success

```
#16A34A
```

Warning

```
#D97706
```

Danger

```
#DC2626
```

Blue

```
#2563EB
```

Gray

```
#64748B
```

Background

```
#F8FAFC
```

Cards

```
#FFFFFF
```

---

# 19. Typography

Preferred font

```
Inter
```

Fallback

```
sans-serif
```

Hierarchy

Page Title

36px

Section Title

24px

Card Title

18px

Body

14–16px

Caption

12px

---

# 20. Icons

Use Heroicons consistently.

Icons should help recognition rather than decoration.

Every sidebar item should have an icon.

Every dashboard card should have an icon.

Avoid mixing multiple icon libraries.

---

# 21. Responsive Design

Three target layouts

Desktop

≥1280px

Tablet

768–1279px

Mobile

≤767px

Tables become cards on mobile whenever practical.

Buttons become full width.

Grids collapse naturally.

---

# 22. Sidebar Behavior

Pages should never stretch when sidebar expands.

Instead

```
max-w-7xl

mx-auto

overflow-x-auto
```

should control layout width.

This issue was discovered and fixed across multiple modules.

---

# 23. PDF Design

Generated PDFs should follow official university branding.

Current PDFs

- Admit Card
- Payment Receipt
- Result Sheet

Include

University logo

University colors

Student information

Professional layout

Signature areas

Footer

---

# 24. Dashboard Principles

Every dashboard should answer

"What should this user do next?"

Examples

Student

View attendance

Download admit card

Submit assignment

Faculty

Take attendance

Upload materials

Submit marks

Accounts

Receive payment

Print receipt

Apply waiver

Exam Controller

Publish routine

Assign hall duty

Generate seat plan

---

# 25. Current UI Status

Completed

✓ Student Dashboard

✓ Faculty Dashboard

✓ Accounts Dashboard

✓ Exam Controller Dashboard

✓ Student Finance Profile

✓ Responsive layouts

✓ Modern cards

✓ PDF styling

✓ Mobile support

✓ Sidebar navigation

✓ Modern table styling

---

# 26. Known Improvements

Still planned

- Dark mode
- Theme customization
- Global search
- Notification center
- Better charts
- Calendar widgets
- Advanced analytics
- Accessibility improvements
- Keyboard shortcuts
- User preferences

---

# 27. Design Principles

Every new page added to the portal should follow these principles.

- Maintain consistent spacing.
- Reuse existing components whenever possible.
- Keep interfaces simple.
- Avoid overcrowding pages.
- Prioritize the most important actions.
- Design mobile-first while optimizing for desktop.
- Keep visual language consistent across all modules.

Consistency is more important than visual complexity. A familiar interface reduces the learning curve for students, faculty, and administrative staff while making the system easier to maintain over time.