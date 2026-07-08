# Order Management System API Workflow

This document describes the backend API responsibilities and the customer order/payment workflow.

## Roles

Customer:

- Register and log in.
- Browse products.
- Place orders.
- View only personal orders.
- Pay for reserved orders.
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
| `POST /api/v1/orders/` | Yes | Yes | Creates an order and reserves inventory when stock is available. |
| `GET /api/v1/orders/{id}/` | Own order | Any order | Owner/admin permission. |
| `PATCH /api/v1/orders/{id}/status/` | No | Yes | Admin-only status update. |
| `GET /api/v1/payments/` | Own transactions | All transactions | Scoped through order owner. |
| `POST /api/v1/payments/initiate/` | Own payable order | Any payable order | Creates and processes a payment transaction. |
| `GET /api/v1/payments/{id}/` | Own transaction | Any transaction | Owner/admin permission. |
| `POST /api/v1/payments/{id}/retry/` | Own failed transaction | Any failed transaction | Retries and processes a failed payment transaction. |

## Customer Journey

```text
Login
  -> Browse products
  -> POST /api/v1/orders/
  -> Order INVENTORY_RESERVED
  -> Open Orders page
  -> Click Pay
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

The API creates an order and immediately runs inventory reservation. It does not trust a submitted `user_id`; the order owner is always `request.user`. If stock is available, the response has status `INVENTORY_RESERVED` and the customer can pay from the Orders page. If stock is unavailable, the order becomes `OUT_OF_STOCK` and inventory is unchanged.

## Inventory Reservation

The order service:

1. Locks the order row.
2. Locks requested product rows in ID order.
3. Aggregates requested quantities per product.
4. Verifies stock is available.
5. Creates order items.
6. Decrements stock using database-side `F()` updates.
7. Stores `total_amount`.
8. Marks the order `INVENTORY_RESERVED`.

If stock is unavailable, the order becomes `OUT_OF_STOCK` and inventory is unchanged.

## Payment Processing

Payment starts only when the customer explicitly pays for an order through `POST /api/v1/payments/initiate/`.
The payment service:

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

Retry is allowed only for failed transactions. The endpoint increments `retry_count`, sets the transaction back to `PENDING`, marks the order `PAYMENT_PROCESSING`, and processes the payment immediately.

## Backend Architecture Notes

Views authenticate users, validate payloads, call services, and return serialized responses. Services own business rules and workflow orchestration. Repositories keep common query patterns in one place.
