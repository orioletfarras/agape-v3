# Agape V3

FastAPI application with layered architecture and AWS Aurora MySQL.

## Architecture

This project follows a clean layered architecture with separation of concerns:

```
app/
├── api/                    # Presentation Layer
│   └── v1/                # API v1 endpoints
│       └── users.py       # User endpoints
├── application/           # Application Layer
│   ├── schemas/          # Pydantic schemas (DTOs)
│   └── services/         # Business logic services
├── domain/               # Domain Layer
│   ├── entities/        # Domain entities
│   └── interfaces/      # Repository interfaces
└── infrastructure/      # Infrastructure Layer (Separated)
    ├── config/         # Settings and configuration
    ├── database/       # Database connection
    │   ├── models/    # SQLAlchemy models
    │   └── repositories/ # Repository implementations
    └── aws/           # AWS integrations
```

## Tech Stack

- **FastAPI**: Modern async web framework
- **SQLAlchemy 2.0**: ORM with async support
- **Alembic**: Database migrations
- **Aurora MySQL**: AWS managed database
- **Pydantic**: Data validation
- **Docker**: Containerization for development

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- AWS Aurora MySQL cluster (for production)

## Local Development Setup

### 1. Clone and setup environment

```bash
# Copy environment variables
cp .env.example .env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start local database with Docker

```bash
# Start MySQL container
docker-compose up -d mysql

# Wait for MySQL to be ready (check with)
docker-compose logs -f mysql
```

### 3. Run database migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run the application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker Compose (full stack)
docker-compose up
```

The API will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Production Deployment (Aurora MySQL)

### 1. Update environment variables

Edit `.env` and uncomment the Aurora configuration:

```bash
# Production - Aurora MySQL
DATABASE_URL=mysql+aiomysql://admin:Pwn20141130!@database-2.cluster-csf25ija4rhk.eu-south-2.rds.amazonaws.com:3306/agape_prod
DATABASE_READER_URL=mysql+aiomysql://admin:Pwn20141130!@database-2.cluster-ro-csf25ija4rhk.eu-south-2.rds.amazonaws.com:3306/agape_prod
```

### 2. Create database schema

```bash
# Connect to Aurora and create database
mysql -h database-2.cluster-csf25ija4rhk.eu-south-2.rds.amazonaws.com -u admin -p
CREATE DATABASE agape_prod;
EXIT;

# Run migrations
alembic upgrade head
```

### 3. Deploy application

```bash
# Build Docker image
docker build -t agape-v3 .

# Run container
docker run -d \
  --name agape-api \
  -p 8000:8000 \
  --env-file .env \
  agape-v3
```

## API Endpoints

### Users

- `POST /api/v3/users/` - Create user
- `GET /api/v3/users/` - List users (with pagination)
- `GET /api/v3/users/{user_id}` - Get user by ID
- `PUT /api/v3/users/{user_id}` - Update user
- `DELETE /api/v3/users/{user_id}` - Delete user

### Example requests

```bash
# Create user
curl -X POST "http://localhost:8000/api/v3/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe"
  }'

# Get all users
curl "http://localhost:8000/api/v3/users/"

# Get user by ID
curl "http://localhost:8000/api/v3/users/1"

# Update user
curl -X PUT "http://localhost:8000/api/v3/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "is_active": false
  }'

# Delete user
curl -X DELETE "http://localhost:8000/api/v3/users/1"
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_user_service.py
```

## Project Structure Details

### Domain Layer
- Contains business entities and interfaces
- No dependencies on other layers
- Pure Python domain logic

### Application Layer
- Contains use cases and business logic
- Depends on domain layer
- Defines DTOs (Data Transfer Objects) with Pydantic

### Infrastructure Layer (Separated)
- Database implementations
- External service integrations
- Configuration management
- Implements interfaces from domain layer

### API Layer
- HTTP endpoints
- Request/response handling
- Dependency injection
- FastAPI routers

## Aurora MySQL Read Replicas

The application supports Aurora read replicas for better performance:

```python
# For write operations (uses writer endpoint)
from app.infrastructure.database import get_db

# For read-only operations (uses reader endpoint if configured)
from app.infrastructure.database import get_reader_db
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | agape-v3 |
| `ENVIRONMENT` | Environment (development/production) | development |
| `DATABASE_URL` | Primary database URL (writer) | - |
| `DATABASE_READER_URL` | Read replica URL (optional) | None |
| `DB_POOL_SIZE` | Connection pool size | 20 |
| `SECRET_KEY` | JWT secret key | - |
| `AWS_REGION` | AWS region | eu-south-2 |

## License

MIT
