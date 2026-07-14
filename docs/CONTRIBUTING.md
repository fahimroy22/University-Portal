# Contributing to Smart University Portal

Thank you for your interest in contributing to the **Smart University Portal**.

This project is a Django-based University ERP designed to manage academic, administrative, financial, examination, and student services through a unified platform. Contributions should preserve the project's modular architecture, role-based permissions, consistent UI design, and workflow integrity.

---

# Code of Conduct

Please be respectful, constructive, and professional in all discussions, code reviews, and pull requests.

---

# Before You Start

Before contributing:

1. Check the existing Issues and Roadmap.
2. Create (or select) an issue before starting work.
3. Keep pull requests focused on a single feature or fix.
4. Avoid mixing unrelated changes.
5. Never commit secrets, databases, uploaded media, virtual environments, or generated files.

---

# Development Requirements

The project has been tested with:

- Python 3.14
- Django 6.x
- Node.js
- npm
- Git

---

# Development Setup

## Clone the repository

```bash
git clone https://github.com/fahimroy22/University-Portal.git
cd University-Portal
```

## Create a virtual environment

macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

## Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Install frontend dependencies

```bash
npm install
```

---

## Apply database migrations

```bash
python manage.py migrate
```

---

## Create an administrator account

```bash
python manage.py createsuperuser
```

---

## Verify the installation

```bash
python manage.py check
```

---

## Run the development server

```bash
python manage.py runserver
```

The application will be available at:

```
http://127.0.0.1:8000/
```

---

# Branch Naming

Always create a new branch before beginning work.

```bash
git checkout -b feature/your-feature-name
```

Recommended prefixes:

| Prefix | Purpose |
|---------|----------|
| feature/ | New functionality |
| fix/ | Bug fixes |
| ui/ | UI or UX improvements |
| refactor/ | Internal code improvements |
| docs/ | Documentation |
| test/ | Testing |

Examples:

```
feature/result-correction-workflow
feature/course-registration
fix/faculty-mark-review
ui/student-dashboard
docs/update-readme
```

---

# Commit Messages

Use concise, meaningful, imperative commit messages.

Good examples:

```
Add faculty mark review workflow

Fix student dashboard pagination

Improve exam controller correction layout

Update installation documentation
```

Avoid:

```
update

changes

fix

stuff
```

---

# Coding Guidelines

## Python & Django

- Follow PEP 8 whenever practical.
- Use descriptive variable and function names.
- Keep business logic out of templates.
- Protect all views with authentication.
- Validate object ownership instead of relying only on user roles.
- Preserve historical academic and financial records.
- Keep reusable logic inside helpers, services, or model methods.

---

## HTML Templates

- Follow the existing design system.
- Maintain responsive layouts.
- Prefer reusable components.
- Avoid unnecessary nesting.
- Keep spacing consistent.
- Use semantic HTML.

---

## CSS / Tailwind

- Reuse existing utility classes.
- Avoid inline styling.
- Maintain consistent spacing.
- Follow the established color palette.

---

## JavaScript

- Keep scripts modular.
- Avoid unnecessary global variables.
- Prefer progressive enhancement.

---

# Database Changes

If modifying models:

```bash
python manage.py makemigrations
python manage.py migrate
```

Before committing:

- Review generated migrations.
- Preserve existing data.
- Maintain referential integrity.
- Never edit production data inside migrations unless absolutely necessary.

---

# Testing

Before submitting a pull request, run:

```bash
python manage.py check

python manage.py test
```

Also verify manually:

- Authentication
- Role permissions
- Direct URL restrictions
- Form validation
- Empty states
- Error handling
- Mobile responsiveness
- Existing workflows

---

# Pull Request Checklist

Before opening a pull request, ensure:

- [ ] One focused change per PR
- [ ] Application starts successfully
- [ ] `python manage.py check` passes
- [ ] Tests pass
- [ ] UI is responsive
- [ ] Existing workflows remain functional
- [ ] Documentation updated if needed
- [ ] Screenshots included for UI changes
- [ ] No secrets committed
- [ ] No database files committed
- [ ] No media uploads committed
- [ ] No virtual environments committed

---

# Pull Request Description

Please include:

- Summary of the change
- Reason for the change
- Affected modules
- Testing performed
- Screenshots (if applicable)
- Migration notes (if applicable)

---

# Reporting Bugs

Please include:

- Title
- User role
- Page or URL
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots
- Browser
- Operating system
- Relevant logs (without sensitive information)

---

# Security

Do **not** submit public issues containing:

- Passwords
- Secret keys
- API keys
- Access tokens
- Student personal information
- Financial records
- Uploaded confidential documents

Report sensitive vulnerabilities privately to the repository owner.

---

# License

By contributing to this repository, you agree that your contributions will be licensed under the project's MIT License.
