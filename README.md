# Epic Events CRM

A secure Customer Relationship Management (CRM) system for Epic Events, a company specializing in event organization. This command-line application allows teams to manage clients, contracts, and events with role-based access control.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Role-Based Access Control**: Three departments with specific permissions
  - **Management**: Full access to all features
  - **Commercial**: Manage clients and contracts
  - **Support**: Manage assigned events
- **Client Management**: Create, update, and track client information
- **Contract Management**: Handle contracts with payment tracking
- **Event Management**: Organize and track events with support assignment
- **Security**: SQL injection prevention, principle of least privilege
- **Logging**: Comprehensive logging with Sentry integration

## Technology Stack

- **Python 3.12+**
- **SQLModel** (Pydantic-compatible ORM)
- **SQLite** database
- **Click** for CLI interface
- **Rich** for enhanced terminal output
- **JWT** for authentication
- **Argon2** for password hashing
- **Sentry** for error tracking

## Installation

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/epic-events-crm.git
cd epic-events-crm
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Copy the environment configuration:
```bash
cp .env.example .env
```

4. Edit `.env` and configure your settings:
```env
DATABASE_URL=sqlite:///./epicevents.db
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
SENTRY_DSN=your-sentry-dsn-here  # Optional
```

5. Initialize the database:
```bash
poetry run python epicevents/scripts/init_db.py
```

This will create the database tables and prompt you to create an initial admin user.

6. (Optional) Create sample data for testing:
```bash
poetry run python epicevents/scripts/init_db.py --sample-data
```

## Usage

### Authentication

Login to the system:
```bash
poetry run epicevents auth login
```

Check current user:
```bash
poetry run epicevents auth whoami
```

Logout:
```bash
poetry run epicevents auth logout
```

### Client Management

List all clients:
```bash
poetry run epicevents client list
```

Create a new client (Commercial only):
```bash
poetry run epicevents client create
```

Update a client:
```bash
poetry run epicevents client update <client_id> --email new@email.com
```

Search clients:
```bash
poetry run epicevents client search "company name"
```

### Contract Management

List contracts:
```bash
poetry run epicevents contract list
poetry run epicevents contract list --unsigned  # Show only unsigned contracts
poetry run epicevents contract list --unpaid    # Show only unpaid contracts
```

Create a contract (Management only):
```bash
poetry run epicevents contract create
```

Sign a contract:
```bash
poetry run epicevents contract sign <contract_id>
```

Update payment:
```bash
poetry run epicevents contract payment <contract_id> --amount 5000
```

### Event Management

List events:
```bash
poetry run epicevents event list
poetry run epicevents event list --without-support  # Events without support
poetry run epicevents event list --upcoming         # Upcoming events only
```

Create an event (Commercial only, for signed contracts):
```bash
poetry run epicevents event create
```

Assign support to an event (Management only):
```bash
poetry run epicevents event assign-support <event_id> --support-id <user_id>
```

Update an event (Support only for assigned events):
```bash
poetry run epicevents event update <event_id> --location "New Location"
```

### User Management (Management Only)

List all users:
```bash
poetry run epicevents user list
```

Create a new user:
```bash
poetry run epicevents user create
```

Update user information:
```bash
poetry run epicevents user update <user_id> --department SUPPORT
```

Reset user password:
```bash
poetry run epicevents user reset-password <user_id>
```

Delete a user:
```bash
poetry run epicevents user delete <user_id>
```

## Department Permissions

### Management Department
- **Full access** to all features
- Create, update, and delete users
- Create and modify all contracts
- Assign support contacts to events
- View all data

### Commercial Department  
- Create new clients (automatically assigned to them)
- Update their own clients
- Update contracts for their clients
- Create events for signed contracts
- View all clients, contracts, and events

### Support Department
- Update events assigned to them
- View all clients, contracts, and events
- Cannot create or delete any data

## Security Features

- **Password Security**: Passwords are hashed using Argon2
- **JWT Authentication**: Stateless authentication with expiring tokens
- **SQL Injection Prevention**: Using SQLModel ORM with parameterized queries
- **Principle of Least Privilege**: Role-based access control
- **Secure Token Storage**: Local token file with appropriate permissions
- **Input Validation**: Pydantic models for data validation
- **Audit Logging**: All critical actions are logged via Sentry

## Database Schema

The application uses the following main entities:

- **Users**: System users with department assignments
- **Clients**: Customer information and commercial assignments
- **Contracts**: Financial agreements with clients
- **Events**: Scheduled events with support assignments

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black epicevents/
poetry run flake8 epicevents/
```

### Type Checking

```bash
poetry run mypy epicevents/
```

## Project Structure

```
epicevents/
├── app/
│   ├── auth/           # Authentication and authorization
│   ├── models/         # Domain models
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── utils/          # Utilities and helpers
│   └── database.py     # Database configuration
├── cli/                # CLI commands
├── scripts/            # Utility scripts
│   └── init_db.py      # Database initialization
└── tests/              # Test suite
```

## Error Handling

The application includes comprehensive error handling:
- User-friendly error messages
- Detailed logging for debugging
- Sentry integration for production monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is developed for Epic Events as part of the OpenClassrooms Python Developer program.

## Support

For issues or questions, please contact the development team or create an issue in the GitHub repository.