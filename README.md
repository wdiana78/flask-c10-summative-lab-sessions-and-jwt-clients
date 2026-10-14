# Productivity Journal API

A Flask REST API for a productivity journaling application. Users can register, authenticate with JSON Web Tokens (JWT), and manage their personal journal entries.

## Features

- User registration and login
- Secure password hashing with Flask-Bcrypt
- JWT authentication and protected routes
- Journal entry creation, retrieval, updating, and deletion (CRUD)
- Pagination for journal entries
- User ownership and access controls
- Database migrations using Flask-Migrate
- Database seeding with sample data
- Automated tests using pytest

## Technology Stack

- Python 3.12
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Migrate
- Flask-Bcrypt
- Flask-JWT-Extended
- python-dotenv
- Pipenv
- pytest

## Project Structure

```text
flask-c10-summative-lab-sessions-and-jwt-clients/
├── client-with-jwt/
├── client-with-sessions/
├── server/
│   ├── .gitignore
│   ├── Pipfile
│   ├── Pipfile.lock
│   ├── app.py
│   ├── models.py
│   ├── seed.py
│   ├── migrations/
│   │   └── versions/
│   └── tests/
│       └── test_app.py
└── README.md
```

The `.env` file, SQLite database, and virtual environment are local development files and are excluded from version control.

## Setup

Clone the repository and enter the backend directory:

```bash
git clone https://github.com/wdiana78/flask-c10-summative-lab-sessions-and-jwt-clients.git
cd flask-c10-summative-lab-sessions-and-jwt-clients/server
```

Install the dependencies recorded in the project's Pipenv files:

```bash
pipenv install --deploy
```

Create a `.env` file inside `server/` with a strong, randomly generated secret:

```text
JWT_SECRET_KEY=your-generated-secret
```

Replace `your-generated-secret` with your own secret. Never commit the actual `.env` file or expose its contents.

## Database Setup

Apply the included database migrations:

```bash
pipenv run flask --app app db upgrade
```

If you change the database models, generate and apply a new migration:

```bash
pipenv run flask --app app db migrate -m "Describe the change"
pipenv run flask --app app db upgrade
```

## Seed Data

Populate the database with demonstration data:

```bash
pipenv run python seed.py
```

The seed script creates a demonstration user and sample journal entries.

- **Username:** `demo_user`
- **Password:** `DemoPass123`

These credentials are for local demonstration only. Do not use them in a production deployment.

## Run the API

From the `server/` directory:

```bash
pipenv run python app.py
```

The development server runs at:

http://127.0.0.1:5555

## API Endpoints

| Method | Endpoint                      | Description                               |
| ------ | ----------------------------- | ----------------------------------------- |
| GET    | `/`                           | Check API availability                    |
| POST   | `/signup`                     | Register a new user                       |
| POST   | `/login`                      | Authenticate a user                       |
| GET    | `/me`                         | Retrieve the authenticated user's details |
| POST   | `/journal_entries`            | Create a journal entry                    |
| GET    | `/journal_entries`            | List journal entries with pagination      |
| GET    | `/journal_entries/<entry_id>` | Retrieve one journal entry                |
| PATCH  | `/journal_entries/<entry_id>` | Update a journal entry                    |
| DELETE | `/journal_entries/<entry_id>` | Delete a journal entry                    |

## Authentication

Protected routes require a valid JWT in the HTTP Authorization header:

```text
Authorization: Bearer <token>
```

The signup and login endpoints return a token after successful authentication.

Signup requires these fields:

```json
{
  "username": "your_username",
  "password": "your_password",
  "password_confirmation": "your_password"
}
```

The password and password confirmation must match.

## Journal Entries

Each journal entry contains:

- `id`: unique entry identifier
- `title`: entry title
- `content`: journal text
- `mood`: recorded mood
- `user_id`: identifier of the entry's owner

Example request body for creating a journal entry:

```json
{
  "title": "Daily Reflection",
  "content": "I made progress on my priorities today.",
  "mood": "Hopeful"
}
```

### Pagination

Use query parameters to control pagination:

```text
GET /journal_entries?page=1&per_page=10
```

The API returns the entries and pagination metadata, including the current page, page size, total entries, and whether additional pages exist. The page size must be between 1 and 100.

## Security

- Passwords are hashed before storage.
- Protected routes require JWT authentication.
- Journal queries are restricted to the authenticated user's entries.
- The JWT secret is stored outside the source code in `.env`.
- Flask debug mode is intended for local development only.

## Testing

Run the backend test suite from the `server/` directory:

```bash
pipenv run pytest -q
```

The test suite covers the API health endpoint, signup validation, duplicate usernames, login, JWT-protected routes, journal CRUD, ownership restrictions, and pagination validation.

## Development Notes

This project is configured for local development. Production deployment requires an appropriate production WSGI server, secure secret management, and production database configuration.
