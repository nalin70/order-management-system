# Order Management System

A Django REST Framework order management system with JWT authentication, role-based access control, inventory reservation, explicit user-driven payment, MySQL persistence, Swagger documentation, Docker Compose, and a minimal React frontend.

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
[MySQL]
```

The backend is organized into modular Django apps:

- `authentication`: custom user model, JWT login/register/refresh/profile, admin user management.
- `inventory`: product CRUD, stock validation, admin-only writes.
- `orders`: order creation, ownership scoping, inventory reservation, lifecycle status.
- `payments`: payment transactions, simulated payment processing, retry support.

## Technology Choices

- Django + DRF: stable API framework with serializers, permissions, test tools, and admin support.
- SimpleJWT: stateless JWT access/refresh authentication.
- MySQL: assignment-compatible relational database for orders, stock, and transaction logs.
- Celery + Redis: optional worker support for background task experiments.
- React + Vite: lightweight frontend for customer/admin workflows.
- Docker Compose: reproducible local stack with backend, database, optional worker/Redis, and frontend.
- drf-yasg: Swagger/OpenAPI documentation.

## Order And Payment Flow

1. Customer calls `POST /api/v1/orders/`.
2. API creates the order, validates stock, reserves inventory, and marks it `INVENTORY_RESERVED`.
3. Customer opens the Orders page and clicks Pay for that order.
4. `POST /api/v1/payments/initiate/` creates and processes a payment transaction.
5. Simulated payment marks the transaction `SUCCESS` and order `COMPLETED`, or transaction `FAILED` and order `PAYMENT_FAILED`.
6. Failed payments can be retried from the Payments page or paid again from the Orders page.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py runserver
```

The normal order/payment workflow does not require Redis, Celery, or any Celery-related `.env` toggle.

Optional: run the Celery worker only if you are experimenting with background tasks:

```bash
docker compose up -d redis
celery -A config worker --loglevel=info
```

Run MySQL locally before running migrations. The command above starts the database from Docker
Compose and exposes MySQL on `127.0.0.1:3306`.

If you use an existing local MySQL installation instead of Docker Compose, create a database
and user matching `.env` before running migrations:

```sql
CREATE DATABASE order_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'oms_user'@'localhost' IDENTIFIED BY 'oms_password';
GRANT ALL PRIVILEGES ON order_management.* TO 'oms_user'@'localhost';
FLUSH PRIVILEGES;
```

If `.env` points at an AWS RDS host, `python manage.py migrate` will only work when that
instance is running and accepts inbound TCP traffic on port `3306` from your current machine.

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
- Redis: `localhost:6379` when the optional Redis service is running

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
- Runtime secrets and database settings are environment-driven.

## Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Tests use an in-memory cache instead of Redis.

See [docs/api_workflow.md](docs/api_workflow.md) for the detailed API workflow.
