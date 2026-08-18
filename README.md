# Contacts Address Book

A small full-stack contact manager built for the AVB technical assessment. It follows the supplied Figma layout and supports listing, viewing, adding, editing, searching, favoriting, exporting, deleting, and restoring contacts. Each contact can have optional company, phone, and birthday information along with any number of email addresses.

## Stack

- Vanilla HTML, CSS, and JavaScript
- Python and Flask
- SQLAlchemy
- SQLite
- Pytest

The frontend does not use React, Vue, Angular, or another JavaScript framework.

## Run it locally

Python 3.9 or newer is supported.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
flask --app app seed
flask --app app run --debug
```

Open `http://127.0.0.1:5000` in a browser.

The `seed` command adds six sample contacts so the layout is easy to review. It is safe to skip if you want to start with an empty address book.

## Run the tests

```bash
pytest
```

The tests use a separate temporary SQLite database. They do not touch local development data.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/contacts` | List favorites first, then sort by name |
| `GET` | `/api/contacts?search=ana` | Search by name, company, or phone |
| `GET` | `/api/contacts/export` | Download active contacts as CSV |
| `GET` | `/api/contacts/:id` | Get one contact and its emails |
| `POST` | `/api/contacts` | Create a contact |
| `PUT` | `/api/contacts/:id` | Update a contact |
| `PATCH` | `/api/contacts/:id/favorite` | Add or remove a contact from favorites |
| `DELETE` | `/api/contacts/:id` | Soft-delete a contact |
| `POST` | `/api/contacts/:id/restore` | Restore a deleted contact |

Example request body:

```json
{
  "first_name": "Craggy",
  "last_name": "Bramble",
  "company": "Marcham & Co.",
  "phone": "212-555-0138",
  "birthday": "1988-10-07",
  "emails": [
    "craggy.bramble@gmail.com",
    "cbramble@marcham.com"
  ]
}
```

## Database design

The database has two tables:

```text
contacts
  id
  first_name
  last_name
  company
  phone
  birthday
  is_favorite
  deleted_at
  created_at
  updated_at

emails
  id
  contact_id
  address
```

`emails.contact_id` is a foreign key to `contacts.id`. This is a one-to-many relationship: one contact can own several email rows. A deleted contact is marked with `deleted_at` and excluded from normal queries, which keeps its email rows available for Undo.

## Validation and user behavior

- First and last name are required in both the browser and the API.
- Company, phone, and birthday are optional. Phone numbers allow common formatting, and birthdays cannot be future dates.
- Email addresses are optional, but every supplied address must be valid.
- Duplicate emails on the same contact are rejected without regard to letter case.
- The UI requires confirmation before deleting a contact.
- Favorites appear before other contacts while both groups stay alphabetical.
- A deleted contact can be restored from the seven-second Undo notification.
- CSV export includes contact details and combines multiple email addresses into one portable field.
- Loading, empty, search-empty, validation, and server-error states are handled.
- User-entered names are added with `textContent`, not HTML, to avoid injecting markup into the page.
- Desktop uses the Figma's side-by-side layout. On smaller screens, the list and details become separate views so a long contact list never pushes the selected contact below it.
- All controls have accessible labels and visible keyboard focus styles.

## Main design decisions

The list endpoint returns only contact summaries. The detail endpoint returns the email collection. That keeps the list response small and gives each endpoint one clear job.

An update replaces the contact's email collection in one database transaction. For this application, that is easier to reason about than sending a separate API request for every email field. If validation fails, none of the changes are committed.

Delete is implemented as a soft delete. Normal list, detail, search, and export queries exclude rows with a deletion timestamp. This creates a useful safety net without requiring a complicated history system. A larger production app would also add a retention policy to permanently purge old deleted records.

SQLite keeps setup simple for the assessment. SQLAlchemy separates the application code from most database-specific details, so moving to PostgreSQL later would mainly involve configuration and a proper migration process.

## Deployment

The app can be deployed as a Railway service from this repository. The `Procfile` creates the sample data when the database is empty and starts Flask with Gunicorn.

For persistent SQLite data, attach a Railway volume at `/data` and add this environment variable:

```text
DATABASE_URL=sqlite:////data/contacts.db
```

SQLite is suitable for this small assessment. A production system with multiple app instances should use PostgreSQL because every instance needs to share the same database and SQLite permits only limited concurrent writes.
