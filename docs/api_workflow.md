# Order Management System API Workflow

This document describes the backend API responsibilities and business workflow for the Django REST Framework Order Management System.

## User roles

### Customer

Customers can:

- Register and log in.
- Browse products.
- Place orders for one or more products.
- View only their own orders.
- Initiate payment for their own orders.
- Retry failed payments for their own payment transactions.
- View their own payment transaction history.

### Admin

Admins can:

- Create, update, and delete products.
- View all orders.
- Update order status.
- View all payment transactions.
- Manage inventory through product stock changes.

## Role-based API access

| API | Customer | Admin | Notes |
| --- | --- | --- | --- |
| `POST /api/auth/register/` | Yes | Yes | Creates a customer account. |
| `POST /api/auth/login/` | Yes | Yes | Returns JWT access and refresh tokens. |
| `GET /api/v1/products/` | Yes | Yes | Product browsing is read-only for customers. |
| `POST /api/v1/products/` | No | Yes | Admin product creation. |
| `PATCH /api/v1/products/{id}/` | No | Yes | Admin inventory and product updates. |
| `DELETE /api/v1/products/{id}/` | No | Yes | Admin product deletion. |
| `GET /api/v1/orders/` | Own orders | All orders | Uses the authenticated user to scope results. |
| `POST /api/v1/orders/` | Yes | Yes | Creates an order for `request.user`; do not send `user_id`. |
| `GET /api/v1/orders/{id}/` | Own order only | Any order | Object-level owner/admin permission applies. |
| `PATCH /api/v1/orders/{id}/status/` | No | Yes | Admin-only status update. |
| `GET /api/v1/payments/` | Own transactions | All transactions | Uses order ownership for customer scoping. |
| `POST /api/v1/payments/initiate/` | Own order only | Any order | Starts payment for a payable order. |
| `GET /api/v1/payments/{id}/` | Own transaction only | Any transaction | Uses the related order owner for permission. |
| `POST /api/v1/payments/{id}/retry/` | Own failed transaction only | Any failed transaction | Only failed payments can be retried. |

## Customer order journey

```text
Customer Login
↓
Browse Products
↓
Select Product
↓
POST /api/v1/orders/
↓
Inventory Reserved
↓
POST /api/v1/payments/initiate/
↓
Payment Success
↓
Order Completed
```

### 1. Customer login

Customers authenticate with:

```http
POST /api/auth/login/
```

The response includes JWT tokens. The frontend must send the access token as a Bearer token on protected APIs.

### 2. Browse products

Customers fetch products with:

```http
GET /api/v1/products/
```

The products response includes product identifiers, pricing, and stock information that the frontend can use for product selection.

### 3. Create an order

Customers create an order with:

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

The request must not include `user_id`. The backend associates the order with the logged-in customer using `request.user`.

During order creation, the order service:

1. Validates that at least one item was submitted.
2. Locks each selected product row while checking inventory.
3. Validates that each quantity is greater than zero.
4. Verifies that stock is available.
5. Creates one `OrderItem` per requested product.
6. Stores the product price on each order item.
7. Decrements product stock to reserve inventory.
8. Calculates `total_amount` from item price and quantity.
9. Marks the order as `INVENTORY_RESERVED`.

If stock is unavailable, the API returns a validation error and the order is not completed.

### 4. Initiate payment

After the order is created and inventory is reserved, customers initiate payment with:

```http
POST /api/v1/payments/initiate/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "order_id": 123
}
```

The payment endpoint verifies that the order belongs to the authenticated customer unless the requester is an admin. Payment initiation is allowed only when the order is in a payable state such as `PENDING` or `INVENTORY_RESERVED`.

### 5. Payment result and order status

The payment service creates a payment transaction and updates the order status based on the payment result:

- Successful payment: order becomes `COMPLETED`.
- Failed payment: order becomes `PAYMENT_FAILED`.

Customers can retry failed payments with:

```http
POST /api/v1/payments/{payment_id}/retry/
```

## Backend architecture notes

Order creation should stay in the service layer rather than in serializers or views. Views should authenticate the user, validate request payloads, call the service, and return serialized responses. The order service owns business rules such as inventory validation, inventory reservation, order item creation, total calculation, and status transitions.
