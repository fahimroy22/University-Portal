# Contributing to UGV Smart University Portal

Thank you for your interest in contributing to the **UGV Smart University Portal**.

This project is a Django-based university ERP designed around realistic academic and administrative workflows. Contributions should preserve the project's modular architecture, role-based permissions, consistent UI language, and workflow integrity.

## Code of Conduct

Be respectful, constructive, and professional in all discussions, reviews, and contributions.

## Before You Start

1. Check the existing issues and roadmap.
2. Create or select an issue for the work you plan to complete.
3. Avoid combining unrelated changes in one pull request.
4. Do not commit secrets, local databases, uploaded media, virtual environments, or generated files.

## Development Setup

Clone the repository:

```bash
git clone https://github.com/fahimryo22/University-Portal.git
cd University-Portal
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies when required:

```bash
npm install
```

Apply migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

## Branch Naming

Create a new branch before starting work:

```bash
git checkout -b feature/short-feature-name
```

Recommended prefixes:

- `feature/` — new functionality
- `fix/` — bug fixes
- `ui/` — layout and styling improvements
- `refactor/` — internal code improvements
- `docs/` — documentation changes
- `test/` — tests and test data

Examples:

```text
feature/result-correction-audit-log
fix/faculty-review-spacing
ui/student-course-history
docs/update-architecture
```

## Commit Messages

Use short, meaningful, imperative commit messages.

Good examples:

```text
Add faculty result correction review
Fix student course history ordering
Refine exam controller correction layout
Update installation documentation
```

Avoid vague messages such as:

```text
update
changes
fix stuff
```

## Coding Guidelines

### Python and Django

- Follow PEP 8 where practical.
- Use clear function and variable names.
- Keep business logic out of templates.
- Keep views focused and extract reusable logic into helpers or services when needed.
- Protect role-specific views with authentication and permission checks.
- Validate object ownership, not only the user's role.
- Preserve historical academic and financial records.

### Templates and UI

- Reuse the established portal design language.
- Keep layouts responsive.
- Avoid deeply nested cards and unnecessary visual clutter.
- Use the project color palette and consistent status badges.
- Do not change form field names, URL names, POST action values, or template variables without updating the corresponding backend.
- Prefer independent vertical stacks over row-based layouts when card heights differ.
- Test desktop, tablet, and mobile layouts.

### Database Changes

- Create migrations for model changes.
- Review generated migrations before committing.
- Never edit production data directly in a migration unless the migration is specifically designed and tested for that purpose.
- Preserve referential integrity across Students, Course Offerings, Finance, Examinations, and Results.

## Testing

Before submitting a pull request, run:

```bash
python manage.py check
python manage.py test
```

Also manually test:

- Authentication and role access
- Direct URL access restrictions
- Form validation
- Mobile responsiveness
- Existing workflows related to your change
- Empty states and error states

## Pull Request Checklist

Before opening a pull request, confirm that:

- [ ] The branch contains one focused change.
- [ ] The application starts without errors.
- [ ] `python manage.py check` passes.
- [ ] Relevant tests pass.
- [ ] No secrets, databases, media files, or virtual environments are committed.
- [ ] UI changes are responsive.
- [ ] Existing workflows are not broken.
- [ ] Documentation is updated when behavior changes.
- [ ] Screenshots are included for meaningful UI changes.

## Pull Request Description

Include:

- What changed
- Why the change was needed
- Which roles or modules are affected
- How the change was tested
- Screenshots for visual changes
- Any migrations or setup steps

## Reporting Bugs

A useful bug report should include:

- A clear title
- User role
- Page or URL
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshot or terminal error
- Browser and operating system
- Relevant logs with sensitive data removed

## Security

Do not open public issues containing:

- Passwords
- API keys
- Secret keys
- Access tokens
- Student personal data
- Financial records
- Private uploaded documents

Report sensitive issues privately to the repository owner.

## License

By contributing, you agree that your contributions will be licensed under the repository's MIT License.
