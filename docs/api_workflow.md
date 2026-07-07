# Order Management System API Workflow

This document describes the backend API responsibilities and the async customer order/payment workflow.

## Roles

Customer:

- Register and log in.
- Browse products.
- Place orders.
- View only personal orders.
- View and retry personal payment transactions.

Admin:

- Create, update, and delete products.
- View all orders and payments.
- Update order status.
- Manage users.

## Role-Based API Access

| API | Customer | Admin | Notes |
| --- | --- | --- | --- |
| `POST /api/auth/register/` | Yes | Yes | Creates a customer account. |
| `POST /api/auth/login/` | Yes | Yes | Returns JWT access and refresh tokens. |
| `POST /api/auth/refresh/` | Yes | Yes | Refreshes access token. |
| `GET /api/auth/profile/` | Own profile | Own profile | Requires authentication. |
| `GET /api/auth/users/` | No | Yes | Admin user management. |
| `PATCH /api/auth/users/{id}/` | No | Yes | Update role or active state. |
| `GET /api/v1/products/` | Yes | Yes | Public product browsing. |
| `POST /api/v1/products/` | No | Yes | Admin product creation. |
| `PATCH /api/v1/products/{id}/` | No | Yes | Admin product update. |
| `DELETE /api/v1/products/{id}/` | No | Yes | Admin product deletion. |
| `GET /api/v1/orders/` | Own orders | All orders | Scoped by authenticated user. |
| `POST /api/v1/orders/` | Yes | Yes | Creates a pending order and queues processing. |
| `GET /api/v1/orders/{id}/` | Own order | Any order | Owner/admin permission. |
| `PATCH /api/v1/orders/{id}/status/` | No | Yes | Admin-only status update. |
| `GET /api/v1/payments/` | Own transactions | All transactions | Scoped through order owner. |
| `POST /api/v1/payments/initiate/` | Own payable order | Any payable order | Manual payment queue endpoint. |
| `GET /api/v1/payments/{id}/` | Own transaction | Any transaction | Owner/admin permission. |
| `POST /api/v1/payments/{id}/retry/` | Own failed transaction | Any failed transaction | Queues retry task. |

## Customer Journey

```text
Login
  -> Browse products
  -> POST /api/v1/orders/
  -> Order PENDING
  -> Celery reserves inventory
  -> Order INVENTORY_RESERVED
  -> Celery processes payment
  -> Order COMPLETED or PAYMENT_FAILED
```

## Create Order

```http
POST /api/v1/orders/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

The API creates a `PENDING` order and stores requested items. It does not trust a submitted `user_id`; the order owner is always `request.user`.

## Async Inventory Reservation

The `process_order` Celery task:

1. Locks the order row.
2. Locks requested product rows in ID order.
3. Aggregates requested quantities per product.
4. Verifies stock is available.
5. Creates order items.
6. Decrements stock using database-side `F()` updates.
7. Stores `total_amount`.
8. Marks the order `INVENTORY_RESERVED`.

If stock is unavailable, the order becomes `OUT_OF_STOCK` and inventory is unchanged.

## Async Payment Processing

The payment task:

1. Marks the order `PAYMENT_PROCESSING`.
2. Creates a `PaymentTransaction` with `PENDING` status.
3. Simulates payment success/failure.
4. Marks transaction `SUCCESS` and order `COMPLETED`, or transaction `FAILED` and order `PAYMENT_FAILED`.

Payment proof is the presence of a successful `PaymentTransaction`. Order responses also expose computed `is_paid` and `payment_status` fields.

## Retry Failed Payment

```http
POST /api/v1/payments/{payment_id}/retry/
Authorization: Bearer <access-token>
```

Retry is allowed only for failed transactions. The endpoint increments `retry_count`, sets the transaction back to `PENDING`, marks the order `PAYMENT_PROCESSING`, and queues payment processing.

## Backend Architecture Notes

Views authenticate users, validate payloads, call services, and return serialized responses. Services own business rules and task orchestration. Repositories keep common query patterns in one place. Celery tasks call service methods so async and test execution use the same business logic.
