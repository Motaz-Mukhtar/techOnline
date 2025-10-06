# TechOnline E-commerce API Specification

## General Rules and Guidelines

### Base URL
```
http://localhost:5001/api/v1
```

### Authentication
The API supports two authentication methods:

1. **JWT Token Authentication** (for customers)
   - Header: `Authorization: Bearer <jwt_token>`
   - Used for customer-specific operations
   - Token expires in 24 hours
   - Obtained via `/auth/login` endpoint

2. **API Key Authentication** (for admin operations)
   - Header: `Authorization: API-Key <api_key>`
   - Used for administrative operations
   - Provides elevated permissions

### Authorization Levels
- **Public**: No authentication required
- **Optional Auth**: Authentication optional, provides additional features if authenticated
- **Customer Auth**: Requires valid JWT token
- **Admin Auth**: Requires valid API key with admin privileges

### Response Format
All responses are in JSON format with the following structure:
```json
{
  "data": {},
  "message": "string",
  "error": "string" // Only present on errors
}
```

### Error Codes
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication required or failed
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `409`: Conflict - Resource already exists
- `500`: Internal Server Error - Server-side error

### Pagination
Endpoints that return lists support pagination:
- `limit`: Maximum number of results (default varies by endpoint)
- `offset`: Number of results to skip (default: 0)

---

## Authentication Endpoints

### POST /auth/login
**Authorization**: Public
**Description**: Authenticate customer and receive JWT token

**Request Body**:
```json
{
  "email": "string",
  "password": "string"
}
```

**Response** (200):
```json
{
  "token": "jwt_token_string",
  "customer": {
    "id": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "message": "Login successful"
}
```

**Error Responses**:
- `400`: Missing email or password
- `401`: Invalid credentials

---

## Product Endpoints

### GET /products
**Authorization**: Optional Auth
**Description**: Retrieve products with optional filtering

**Query Parameters**:
- `search`: Search term for product name/description
- `category`: Filter by category name
- `min_price`: Minimum price filter (float)
- `max_price`: Maximum price filter (float)
- `in_stock`: Only return products in stock (true/false, default: true)
- `limit`: Maximum results (default: 20)
- `sort_by`: Sort by 'name', 'price', 'created_at' (default: 'name')

**Response** (200):
```json
{
  "products": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "price": "float",
      "stock_quantity": "integer",
      "category_id": "string",
      "is_available": "boolean"
    }
  ]
}
```

### GET /products/{product_id}
**Authorization**: Optional Auth
**Description**: Get specific product details

**Response** (200):
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "price": "float",
  "stock_quantity": "integer",
  "category_id": "string",
  "is_available": "boolean"
}
```

**Error Responses**:
- `404`: Product not found

---

## Customer Endpoints

### GET /customers
**Authorization**: Admin Auth
**Description**: Get all customers (admin only)

**Query Parameters**:
- `limit`: Maximum results (default: 50)
- `offset`: Results to skip (default: 0)

**Response** (200):
```json
{
  "customers": [
    {
      "id": "string",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "created_at": "datetime"
    }
  ]
}
```

### GET /customers/{customer_id}
**Authorization**: Customer Auth
**Description**: Get specific customer details (own profile or admin)

**Response** (200):
```json
{
  "id": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "address": "string",
  "created_at": "datetime"
}
```

**Error Responses**:
- `403`: Access denied (can only view own profile unless admin)
- `404`: Customer not found

### PUT /customers/{customer_id}
**Authorization**: Customer Auth
**Description**: Update customer profile (own profile or admin)

**Request Body**:
```json
{
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "address": "string"
}
```

**Response** (200):
```json
{
  "message": "Customer updated successfully",
  "customer": {
    "id": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string"
  }
}
```

### DELETE /customers/{customer_id}
**Authorization**: Customer Auth
**Description**: Delete customer account (own account or admin)

**Response** (200):
```json
{
  "message": "Customer deleted successfully"
}
```

---

## Cart Endpoints

### GET /carts
**Authorization**: Customer Auth
**Description**: Get user's carts (own carts or all carts for admin)

**Response** (200):
```json
{
  "carts": [
    {
      "id": "string",
      "customer_id": "string",
      "created_at": "datetime",
      "items": []
    }
  ]
}
```

### POST /carts
**Authorization**: Customer Auth
**Description**: Create a new cart for authenticated user

**Response** (201):
```json
{
  "id": "string",
  "customer_id": "string",
  "created_at": "datetime",
  "items": []
}
```

**Error Responses**:
- `409`: Customer already has a cart

### GET /carts/{cart_id}
**Authorization**: Customer Auth
**Description**: Get specific cart details (own cart or admin)

**Response** (200):
```json
{
  "id": "string",
  "customer_id": "string",
  "created_at": "datetime",
  "items": [
    {
      "product_id": "string",
      "quantity": "integer",
      "price": "float"
    }
  ]
}
```

### PUT /carts/{cart_id}
**Authorization**: Customer Auth
**Description**: Update cart details (own cart or admin)

**Request Body**:
```json
{
  "field_to_update": "value"
}
```

### DELETE /carts/{cart_id}
**Authorization**: Customer Auth
**Description**: Delete cart (own cart or admin)

**Response** (200):
```json
{}
```

### POST /carts/{cart_id}/add_product
**Authorization**: Customer Auth
**Description**: Add product to cart (own cart or admin)

**Request Body**:
```json
{
  "product_id": "string",
  "quantity": "integer" // optional, default: 1
}
```

**Response** (200):
```json
{
  "message": "Product added to cart",
  "cart_item": {
    "product_id": "string",
    "quantity": "integer",
    "price": "float"
  }
}
```

---

## Order Endpoints

### GET /orders
**Authorization**: Optional Auth
**Description**: Get orders (own orders for customers, all orders for admin)

**Query Parameters**:
- `customer_id`: Filter by customer ID
- `status`: Filter by order status
- `min_amount`: Minimum order amount (float)
- `max_amount`: Maximum order amount (float)
- `limit`: Maximum results (default: 50)
- `offset`: Results to skip (default: 0)
- `sort_by`: Sort by 'date', 'amount', 'status' (default: 'date')
- `order`: 'asc' or 'desc' (default: 'desc')

**Response** (200):
```json
{
  "orders": [
    {
      "id": "string",
      "customer_id": "string",
      "total_amount": "float",
      "order_status": "string",
      "created_at": "datetime"
    }
  ],
  "pagination": {
    "total": "integer",
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

### POST /orders
**Authorization**: Customer Auth
**Description**: Create new order from cart

**Request Body**:
```json
{
  "cart_id": "string"
}
```

**Response** (201):
```json
{
  "message": "Order created successfully",
  "order": {
    "id": "string",
    "customer_id": "string",
    "total_amount": "float",
    "order_status": "string",
    "created_at": "datetime"
  }
}
```

### GET /orders/{order_id}/status/transitions
**Authorization**: Customer Auth
**Description**: Get valid status transitions for an order

**Response** (200):
```json
{
  "order_id": "string",
  "current_status": "string",
  "valid_transitions": ["string"]
}
```

---

## Review Endpoints

### GET /reviews
**Authorization**: Optional Auth
**Description**: Get product reviews with filtering

**Query Parameters**:
- `product_id`: Filter by product ID
- `customer_id`: Filter by customer ID
- `rating`: Filter by specific rating (1-5)
- `min_rating`: Filter by minimum rating (float)
- `approved_only`: Only approved reviews (true/false, default: true)
- `verified_only`: Only verified purchase reviews (true/false, default: false)
- `limit`: Maximum results (default: 20)
- `offset`: Results to skip (default: 0)
- `sort_by`: Sort by 'date', 'rating', 'helpful' (default: 'date')
- `order`: 'asc' or 'desc' (default: 'desc')

**Response** (200):
```json
{
  "reviews": [
    {
      "id": "string",
      "product_id": "string",
      "customer_id": "string",
      "rate": "float",
      "text": "string",
      "title": "string",
      "is_approved": "boolean",
      "is_verified": "boolean",
      "helpful_count": "integer",
      "created_at": "datetime"
    }
  ],
  "pagination": {
    "total": "integer",
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

### GET /reviews/{review_id}
**Authorization**: Optional Auth
**Description**: Get specific review details

**Response** (200):
```json
{
  "id": "string",
  "product_id": "string",
  "customer_id": "string",
  "rate": "float",
  "text": "string",
  "title": "string",
  "is_approved": "boolean",
  "is_verified": "boolean",
  "helpful_count": "integer",
  "created_at": "datetime"
}
```

### POST /reviews
**Authorization**: Customer Auth
**Description**: Create a new product review

**Request Body**:
```json
{
  "product_id": "string",
  "text": "string",
  "rate": "float", // 1-5
  "title": "string" // optional
}
```

**Response** (201):
```json
{
  "message": "Review created successfully",
  "review": {
    "id": "string",
    "product_id": "string",
    "customer_id": "string",
    "rate": "float",
    "text": "string",
    "title": "string"
  }
}
```

---

## Search Endpoints

### GET /search/products
**Authorization**: Optional Auth
**Description**: Search for products with various filters

**Query Parameters**:
- `q`: Search term for product name/description
- `category_id`: Filter by category ID
- `category_name`: Filter by category name
- `min_price`: Minimum price filter (float)
- `max_price`: Maximum price filter (float)
- `in_stock`: Only return products in stock (true/false, default: true)
- `limit`: Maximum results (default: 20)
- `sort_by`: Sort by 'name', 'price', 'created_at' (default: 'name')

**Response** (200):
```json
{
  "products": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "price": "float",
      "stock_quantity": "integer",
      "category_id": "string"
    }
  ],
  "search_metadata": {
    "query": "string",
    "total_results": "integer",
    "search_time": "float"
  }
}
```

---

## Stock Management Endpoints

### GET /stock/check/{product_id}
**Authorization**: Optional Auth
**Description**: Check stock availability for a product

**Query Parameters**:
- `quantity`: Quantity to check availability for (default: 1)

**Response** (200):
```json
{
  "product_id": "string",
  "requested_quantity": "integer",
  "available_quantity": "integer",
  "is_available": "boolean",
  "stock_status": "string"
}
```

**Error Responses**:
- `400`: Invalid quantity
- `404`: Product not found

---

## Client-Side vs Admin-Side Endpoints Summary

### Client-Side Endpoints (Customer Authentication)
- `POST /auth/login` - Public
- `GET /products` - Optional Auth
- `GET /products/{id}` - Optional Auth
- `GET /customers/{id}` - Customer Auth (own profile)
- `PUT /customers/{id}` - Customer Auth (own profile)
- `DELETE /customers/{id}` - Customer Auth (own account)
- `GET /carts` - Customer Auth (own carts)
- `POST /carts` - Customer Auth
- `GET /carts/{id}` - Customer Auth (own cart)
- `PUT /carts/{id}` - Customer Auth (own cart)
- `DELETE /carts/{id}` - Customer Auth (own cart)
- `POST /carts/{id}/add_product` - Customer Auth (own cart)
- `GET /orders` - Optional Auth (own orders when authenticated)
- `POST /orders` - Customer Auth
- `GET /orders/{id}/status/transitions` - Customer Auth
- `GET /reviews` - Optional Auth
- `GET /reviews/{id}` - Optional Auth
- `POST /reviews` - Customer Auth
- `GET /search/products` - Optional Auth
- `GET /stock/check/{id}` - Optional Auth

### Admin-Side Endpoints (API Key Authentication)
- `GET /customers` - Admin Auth
- `GET /customers/{id}` - Admin Auth (any customer)
- `PUT /customers/{id}` - Admin Auth (any customer)
- `DELETE /customers/{id}` - Admin Auth (any customer)
- `GET /carts` - Admin Auth (all carts)
- `GET /carts/{id}` - Admin Auth (any cart)
- `PUT /carts/{id}` - Admin Auth (any cart)
- `DELETE /carts/{id}` - Admin Auth (any cart)
- `POST /carts/{id}/add_product` - Admin Auth (any cart)
- `GET /orders` - Admin Auth (all orders)

### Notes
- Customers can only access their own resources (carts, orders, profiles) unless they have admin privileges
- Admin users can access all resources across the system
- Some endpoints support both customer and admin access with different permission levels
- Optional auth endpoints provide additional features when authenticated but work without authentication