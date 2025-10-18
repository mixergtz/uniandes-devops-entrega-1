# Blacklist Service

A Flask-based REST API service for managing a global email blacklist. This service allows you to add emails to a blacklist and check if an email is blocked.

## Features

- Add emails to a global blacklist with optional reasons
- Check if an email is blacklisted
- Bearer token authentication
- PostgreSQL/SQLite database support
- Idempotent operations
- Health check endpoint for load balancers

## Requirements

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

## Installation

### 1. Install uv

If you don't have `uv` installed, install it using one of these methods:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip:**
```bash
pip install uv
```

### 2. Clone the repository

```bash
git clone <repository-url>
cd blacklist-service
```

### 3. Install dependencies

Using `uv`, install all project dependencies:

```bash
uv sync
```

This will create a virtual environment and install all dependencies from `pyproject.toml`.

## Configuration

The application uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///local.db` |
| `AUTH_BEARER_TOKEN` | Bearer token for API authentication | `CHANGE_ME_IN_PROD` |
| `RUN_DB_MIGRATIONS` | Auto-run DB migrations on startup (0 or 1) | `0` |

### Example configurations:

**Local SQLite:**
```bash
export DATABASE_URL="sqlite:///local.db"
export AUTH_BEARER_TOKEN="your-secret-token"
```

**PostgreSQL (RDS):**
```bash
export DATABASE_URL="postgresql+psycopg2://username:password@host:5432/database"
export AUTH_BEARER_TOKEN="your-secret-token"
```

## Running the Application

### Option 1: Using Flask development server

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Set environment variables
export DATABASE_URL="sqlite:///local.db"
export AUTH_BEARER_TOKEN="dev-token-123"
export RUN_DB_MIGRATIONS="1"

# Run with Flask
flask --app app run --port 8000
```

### Option 2: Using Gunicorn (recommended for production)

```bash
# Activate the virtual environment
source .venv/bin/activate

# Set environment variables
export DATABASE_URL="sqlite:///local.db"
export AUTH_BEARER_TOKEN="dev-token-123"
export RUN_DB_MIGRATIONS="1"

# Run with Gunicorn
gunicorn wsgi:application -b 0.0.0.0:8000
```

### Option 3: Using uv run (no activation needed)

```bash
# Set environment variables
export DATABASE_URL="sqlite:///local.db"
export AUTH_BEARER_TOKEN="dev-token-123"
export RUN_DB_MIGRATIONS="1"

# Run with uv
uv run gunicorn wsgi:application -b 0.0.0.0:8000
```

## Database Setup

### Automatic migration (for development)

Set the `RUN_DB_MIGRATIONS` environment variable to `1`:

```bash
export RUN_DB_MIGRATIONS="1"
```

The application will automatically create the database schema on startup.

### Manual migration

Use the `manage.py` script:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Set the database URL
export DATABASE_URL="postgresql+psycopg2://user:password@host:5432/database"

# Initialize the database
python manage.py init-db
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the service health status.

**Response:**
```json
{
  "status": "ok"
}
```

### Add Email to Blacklist

```bash
POST /blacklists
```

**Headers:**
```
Authorization: Bearer <your-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
  "blocked_reason": "spam detected"
}
```

**Response (201 Created):**
```json
{
  "message": "Email added to global blacklist"
}
```

**Response (200 OK - Already exists):**
```json
{
  "message": "Email was already on the blacklist"
}
```

### Check if Email is Blacklisted

```bash
GET /blacklists/<email>
```

**Headers:**
```
Authorization: Bearer <your-token>
```

**Response (Blocked):**
```json
{
  "blocked": true,
  "email": "user@example.com",
  "blocked_reason": "spam detected",
  "created_at": "2024-01-15T10:30:00"
}
```

**Response (Not Blocked):**
```json
{
  "blocked": false,
  "email": "user@example.com",
  "blocked_reason": null,
  "created_at": null
}
```

## Testing

Run the test suite using pytest:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run tests
pytest

# Or use uv run
uv run pytest
```

For verbose output:

```bash
pytest -v
```

## Development

### Install development dependencies

Development dependencies (like pytest) are already included when you run `uv sync`.

### Project Structure

```
blacklist-service/
├── app/
│   ├── __init__.py      # Application factory
│   ├── config.py        # Configuration
│   ├── models.py        # Database models
│   ├── routes.py        # API endpoints
│   └── schemas.py       # Request/response schemas
├── tests/
│   └── test_api.py      # API tests
├── instance/            # Instance-specific files (DB, etc.)
├── manage.py            # Database management script
├── wsgi.py              # WSGI entry point
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## Docker

Build and run with Docker:

```bash
# Build the image
docker build -t blacklist-service .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///local.db" \
  -e AUTH_BEARER_TOKEN="your-token" \
  -e RUN_DB_MIGRATIONS="1" \
  blacklist-service
```

## Deployment

This application is designed to be deployed on AWS Elastic Beanstalk, but can run on any platform that supports Python WSGI applications.

### Environment Variables for Production

Make sure to set these environment variables in your production environment:

- `DATABASE_URL`: PostgreSQL connection string
- `AUTH_BEARER_TOKEN`: Strong, secure token
- `RUN_DB_MIGRATIONS`: Set to `0` (manage migrations manually in production)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
