# Order Management System

A Django REST Framework order management system with JWT authentication, role-based access control, async order processing through Celery + Redis, MySQL persistence, Swagger documentation, Docker Compose, and a minimal React frontend.

## Architecture

```text
[React Frontend]
       |
       v
[DRF API / Auth / RBAC]
       |
       +--> Order Service
       +--> Inventory Service
       +--> Payment Service
       |
       v
[Celery Worker] <--> [Redis Queue]
       |
       v
[MySQL]
```

The backend is organized into modular Django apps:

- `authentication`: custom user model, JWT login/register/refresh/profile, admin user management.
- `inventory`: product CRUD, stock validation, admin-only writes.
- `orders`: order creation, ownership scoping, lifecycle status, async workflow trigger.
- `payments`: payment transactions, simulated payment processing, retry support.

## Technology Choices

- Django + DRF: stable API framework with serializers, permissions, test tools, and admin support.
- SimpleJWT: stateless JWT access/refresh authentication.
- MySQL: assignment-compatible relational database for orders, stock, and transaction logs.
- Celery + Redis: queue-backed async workflow for inventory reservation and payment processing.
- React + Vite: lightweight frontend for customer/admin workflows.
- Docker Compose: reproducible local stack with backend, worker, database, Redis, and frontend.
- drf-yasg: Swagger/OpenAPI documentation.

## Async Order Flow

1. Customer calls `POST /api/v1/orders/`.
2. API creates an order with `PENDING` status and stores requested items.
3. Celery `process_order` locks product rows, validates stock, creates order items, decrements stock, and marks the order `INVENTORY_RESERVED`.
4. Celery queues payment processing and marks the order `PAYMENT_PROCESSING`.
5. Payment task creates a `PaymentTransaction`.
6. Simulated payment marks the transaction `SUCCESS` and order `COMPLETED`, or transaction `FAILED` and order `PAYMENT_FAILED`.
7. Failed transactions can be retried through `POST /api/v1/payments/{id}/retry/`.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Run the Celery worker in a second terminal:

```bash
celery -A config worker --loglevel=info
```

Run Redis locally or use Docker Compose.

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Docker Setup

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Swagger: `http://localhost:8000/swagger/`
- MySQL: `localhost:3306`
- Redis: `localhost:6379`

## Key APIs

Authentication:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/profile/`
- `GET /api/auth/users/` admin only
- `PATCH /api/auth/users/{id}/` admin only

Inventory:

- `GET /api/v1/products/`
- `POST /api/v1/products/` admin only
- `PATCH /api/v1/products/{id}/` admin only
- `DELETE /api/v1/products/{id}/` admin only

Orders:

- `POST /api/v1/orders/`
- `GET /api/v1/orders/`
- `GET /api/v1/orders/{id}/`
- `PATCH /api/v1/orders/{id}/status/` admin only

Payments:

- `GET /api/v1/payments/`
- `POST /api/v1/payments/initiate/`
- `GET /api/v1/payments/{id}/`
- `POST /api/v1/payments/{id}/retry/`

## Security And Reliability

- Passwords are hashed with Django's built-in password hasher.
- JWT access/refresh lifetimes are environment configurable.
- Role-based access uses `User.role` with `ADMIN` and `CUSTOMER`.
- Protected APIs return `401` for unauthenticated requests and `403` for forbidden role access.
- Stock reservation uses database transactions, row locks, and `F()` updates.
- Product stock has a database check constraint preventing negative values.
- API throttling, CORS, centralized exception handling, and request IDs are configured.
- Runtime secrets and database/Redis settings are environment-driven.

## Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Tests run Celery work eagerly where needed and use an in-memory cache instead of Redis.

See [docs/api_workflow.md](docs/api_workflow.md) for the detailed API workflow.
