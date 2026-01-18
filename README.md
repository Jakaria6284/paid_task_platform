# Paid Task Platform - Backend

A complete FastAPI backend for a project management platform with role-based access control and payment workflow.

## Features

- **Authentication**: Email/password with JWT tokens
- **Role-based Access**: Admin, Buyer, Developer
- **Project Management**: Create and manage projects
- **Proposal System**: Upwork-style bidding on projects (NEW!)
- **Task Assignment**: Assign tasks to developers with hourly rates
- **Payment Workflow**: Lock task solutions until payment
- **Admin Dashboard**: Comprehensive statistics
- **File Upload**: ZIP file submissions for task solutions

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- Pydantic validation

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/paid_task_platform
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
UPLOAD_DIR=uploads/tasks
```

### 3. Create PostgreSQL Database

```bash
createdb paid_task_platform
```

Or using psql:
```sql
CREATE DATABASE paid_task_platform;
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Create Admin User (Manual)

Since admin registration is blocked via API, you need to create an admin user directly in the database:

```python
# create_admin.py
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.security.jwt import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

# Create session
db = SessionLocal()

# Create admin
admin = User(
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    role=UserRole.ADMIN,
    full_name="Admin User"
)

db.add(admin)
db.commit()
print("Admin user created successfully!")
db.close()
```

Run: `python create_admin.py`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register buyer or developer
- `POST /api/v1/auth/login` - Login and get JWT token

### Projects (Buyer)
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - Get all projects
- `GET /api/v1/projects/{id}` - Get project details
- `GET /api/v1/projects/{id}/tasks` - Get project tasks
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Proposals (NEW - Upwork-style Bidding)
- `POST /api/v1/proposals/` - Submit proposal to project (Developer)
- `GET /api/v1/proposals/my-proposals` - Get my proposals (Developer)
- `GET /api/v1/proposals/project/{id}` - Get all proposals for project (Buyer)
- `POST /api/v1/proposals/{id}/accept` - Accept proposal and hire (Buyer)
- `POST /api/v1/proposals/{id}/reject` - Reject proposal (Buyer)

### Tasks
- `POST /api/v1/tasks/` - Create and assign task (Buyer)
- `GET /api/v1/tasks/my-tasks` - Get assigned tasks (Developer)
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task status (Developer)
- `POST /api/v1/tasks/{id}/submit` - Submit task with ZIP (Developer)
- `GET /api/v1/tasks/{id}/download` - Download solution (Buyer, after payment)

### Payments (Buyer)
- `POST /api/v1/payments/` - Make payment for submitted task
- `GET /api/v1/payments/my-payments` - Get payment history
- `GET /api/v1/payments/{id}` - Get payment details

### Admin
- `GET /api/v1/admin/dashboard` - Get dashboard statistics

## Workflow Example

### 1. Register Users

**Register Buyer:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@example.com",
    "password": "buyer123",
    "role": "buyer",
    "full_name": "John Buyer"
  }'
```

**Register Developer:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "password": "dev123",
    "role": "developer",
    "full_name": "Jane Developer"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@example.com",
    "password": "buyer123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### 3. Create Project (Buyer)

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-commerce Website",
    "description": "Build a modern e-commerce platform with Flutter",
    "expected_hourly_rate": 50.0,
    "expected_duration_hours": 80,
    "tags": ["flutter", "mobile", "ecommerce", "firebase"]
  }'
```

### 4. Developer Browses Open Projects

**Simple browse:**
```bash
curl -X GET "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer DEVELOPER_TOKEN"
```

**Search with filters:**
```bash
# Search for Flutter projects with specific budget
curl -X GET "http://localhost:8000/api/v1/projects/?search=flutter&tags=mobile,ai&min_rate=40&max_rate=60" \
  -H "Authorization: Bearer DEVELOPER_TOKEN"

# Find short-term projects
curl -X GET "http://localhost:8000/api/v1/projects/?max_duration=40&tags=backend" \
  -H "Authorization: Bearer DEVELOPER_TOKEN"
```

### 5. Developer Submits Proposal (NEW!)

```bash
curl -X POST "http://localhost:8000/api/v1/proposals/" \
  -H "Authorization: Bearer DEVELOPER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "cover_letter": "I have 5 years of Flutter experience and have built similar platforms. I can deliver clean, maintainable code.",
    "proposed_hourly_rate": 50.0,
    "estimated_hours": 40
  }'
```

### 6. Buyer Reviews Proposals

```bash
curl -X GET "http://localhost:8000/api/v1/proposals/project/1" \
  -H "Authorization: Bearer BUYER_TOKEN"
```

### 7. Buyer Accepts Best Proposal

```bash
curl -X POST "http://localhost:8000/api/v1/proposals/1/accept" \
  -H "Authorization: Bearer BUYER_TOKEN"
```

### 8. Create Task for Accepted Developer (Buyer)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build Shopping Cart",
    "description": "Implement shopping cart functionality",
    "project_id": 1,
    "developer_id": 2,
    "hourly_rate": 50.0
  }'
```

### 9. Developer Updates Task

```bash
curl -X PUT "http://localhost:8000/api/v1/tasks/1" \
  -H "Authorization: Bearer DEVELOPER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress"
  }'
```

### 10. Developer Submits Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/submit" \
  -H "Authorization: Bearer DEVELOPER_TOKEN" \
  -F "file=@solution.zip" \
  -F "time_spent=8.5"
```

### 11. Buyer Makes Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments/" \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1
  }'
```

### 12. Buyer Downloads Solution

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/1/download" \
  -H "Authorization: Bearer BUYER_TOKEN" \
  --output solution.zip
```

### 13. Admin Views Dashboard

```bash
curl -X GET "http://localhost:8000/api/v1/admin/dashboard" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Project Structure

```
paid-task-platform-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # Database connection
│   ├── dependencies.py      # Auth dependencies
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── crud/                # Database operations
│   ├── api/v1/              # API endpoints
│   ├── security/            # JWT handling
│   └── utils/               # File utilities
├── uploads/tasks/           # Uploaded files
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
└── README.md
```

## Security Notes

- Admin users cannot be created via the registration API
- JWT tokens expire after 7 days (configurable)
- Passwords are hashed using bcrypt
- Role-based access control on all endpoints
- File downloads only after payment verification

## License

MIT