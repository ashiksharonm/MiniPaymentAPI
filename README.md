# Mini Payments API 💳

A **production-style** Mini Payments API demonstrating backend engineering fundamentals for fintech applications. Built as a learning and portfolio project.

> ⚠️ **Disclaimer**: This is NOT a real payment gateway. It does NOT process real payments and should NOT be used for actual financial transactions. Not compliant with PCI-DSS or any banking regulations.

## 🌐 Live Demo

| Resource | URL |
|----------|-----|
| 🚀 Live API (Swagger UI) | [https://mini-payments-api.onrender.com/docs](https://mini-payments-api.onrender.com/docs) |
| 📖 ReDoc | [https://mini-payments-api.onrender.com/redoc](https://mini-payments-api.onrender.com/redoc) |
| ❤️ Health Check | [https://mini-payments-api.onrender.com/health](https://mini-payments-api.onrender.com/health) |

> **Note:** Free-tier Render instances spin down after inactivity. The first request may take ~30 seconds to wake up.
>
> **Demo API Key:** `demo-api-key-12345` (use in the `X-API-Key` header or via the Authorize button in Swagger UI)

## 🎯 Overview

This project demonstrates key backend engineering skills:

- **RESTful API Design** with FastAPI
- **Clean Architecture** (routes → services → models)
- **Database Modeling** with SQLAlchemy ORM
- **FX Currency Conversion** with static rates
- **Idempotent Operations** preventing duplicate transactions
- **Comprehensive Testing** with pytest

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Language | Python 3.10+ |
| Database | SQLite (PostgreSQL-ready) |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| Testing | pytest + httpx |
| Auth | API Key (demo) |

## 📁 Project Structure

```
mini-payments-api/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── routes_users.py     # User endpoints
│   │   └── routes_transactions.py  # Transaction endpoints
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   └── fx_rates.py         # Static FX rates
│   ├── models/
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── transaction.py      # Transaction SQLAlchemy model
│   ├── schemas/
│   │   ├── user.py             # User Pydantic schemas
│   │   └── transaction.py      # Transaction Pydantic schemas
│   ├── services/
│   │   ├── user_service.py     # User business logic
│   │   └── transaction_service.py  # Transaction business logic
│   ├── db/
│   │   ├── base.py             # SQLAlchemy declarative base
│   │   └── session.py          # Database session factory
│   └── tests/
│       ├── conftest.py         # Test fixtures
│       ├── test_users.py       # User API tests
│       └── test_transactions.py  # Transaction API tests
├── alembic/                    # Database migrations
├── requirements.txt
└── README.md
```

## 🏗️ System Architecture

The diagram below is the full architecture in [Eraser.io](https://app.eraser.io) diagram code. Paste it at [app.eraser.io](https://app.eraser.io) to render the interactive diagram.

```
// Eraser.io Diagram Code
// Paste at: https://app.eraser.io/

title Mini Payments API — System Architecture

// ─── Groups ───────────────────────────────────────────────
group Client {
  Client [icon: monitor, color: blue]
}

group API_Layer [label: "FastAPI Application (Render.com)"] {
  CORS_Middleware [icon: shield, color: orange, label: "CORS Middleware"]
  Auth_Middleware [icon: lock, color: red, label: "API Key Auth Middleware"]

  group Routers [label: "Route Handlers"] {
    Users_Router [icon: users, color: green, label: "/users router"]
    Transactions_Router [icon: credit-card, color: purple, label: "/transactions router"]
    Health_Router [icon: activity, color: gray, label: "/health router"]
  }

  group Services [label: "Business Logic Layer"] {
    User_Service [icon: user, color: green, label: "UserService"]
    Transaction_Service [icon: zap, color: purple, label: "TransactionService"]
    FX_Engine [icon: refresh-cw, color: yellow, label: "FX Rate Engine (Static Rates)"]
  }

  group Data_Layer [label: "Data Layer — SQLAlchemy ORM"] {
    User_Model [icon: table, color: green, label: "User Model"]
    Transaction_Model [icon: table, color: purple, label: "Transaction Model"]
  }
}

group Database [label: "Persistence"] {
  SQLite [icon: database, color: gray, label: "SQLite DB (mini_payments.db)"]
}

group Schemas [label: "Pydantic Schemas (Validation)"] {
  UserSchema [icon: file-text, color: green, label: "UserCreate / UserResponse"]
  TransactionSchema [icon: file-text, color: purple, label: "TransactionCreate / TransactionResponse"]
}

// ─── Connections ────────────────────────────────────────────
Client --> CORS_Middleware: HTTP Request
CORS_Middleware --> Auth_Middleware
Auth_Middleware --> Users_Router: Authenticated
Auth_Middleware --> Transactions_Router: Authenticated
Auth_Middleware --> Health_Router: No Auth Required

Users_Router --> UserSchema: Validate Input
Users_Router --> User_Service
User_Service --> User_Model

Transactions_Router --> TransactionSchema: Validate Input
Transactions_Router --> Transaction_Service
Transaction_Service --> FX_Engine: Convert Currency
Transaction_Service --> Transaction_Model
Transaction_Service --> User_Model: Check User Exists

User_Model --> SQLite
Transaction_Model --> SQLite

Users_Router --> Client: JSON Response
Transactions_Router --> Client: JSON Response (with FX converted amount)
Health_Router --> Client: {status: healthy}
```

### Architecture Summary

```
┌──────────────────────────────────────────────────────────┐
│                     HTTP Client                          │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│              FastAPI Application (Render.com)            │
│                                                          │
│  CORS Middleware → API Key Auth Middleware               │
│       │                    │                            │
│  /users router    /transactions router    /health        │
│       │                    │                            │
│  UserService       TransactionService                    │
│       │              │         │                        │
│       │         FX Engine   UserService                 │
│       │              │                                  │
│  ─────────── SQLAlchemy ORM ───────────                 │
│       │                    │                            │
│  User Model       Transaction Model                     │
└───────┬────────────────────┬────────────────────────────┘
        │                    │
┌───────▼────────────────────▼────────────────────────────┐
│               SQLite Database                           │
│         (mini_payments.db)                              │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- pip or pipenv

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ashiksharonm/MiniPaymentAPI.git
   cd MiniPaymentsAPI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API**
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

## 🔐 Authentication

All API endpoints (except health checks) require an API key.

**Default API Key:** `demo-api-key-12345`

Include it in the request header:
```
X-API-Key: demo-api-key-12345
```

## 📡 API Endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Create a new user |
| `GET` | `/users/{user_id}` | Get user by ID |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create transaction with FX conversion |
| `GET` | `/transactions/{id}` | Get transaction by ID |
| `GET` | `/users/{user_id}/transactions` | List user's transactions |
| `PATCH` | `/transactions/{id}/status` | Update transaction status |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint |
| `GET` | `/health` | Health check |

## 💱 FX Rates

The API uses static exchange rates for demonstration:

| From | To | Rate |
|------|-----|------|
| USD | INR | 83.00 |
| USD | EUR | 0.92 |
| USD | GBP | 0.79 |
| EUR | USD | 1.08 |
| EUR | INR | 89.64 |
| INR | USD | 0.012 |
| GBP | USD | 1.27 |

> **Note**: These are fictional rates for demo purposes. A production system would integrate with a real FX provider.

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest app/tests/test_users.py

# Run with coverage
pytest --cov=app
```

## 🔄 Transaction Lifecycle

```
┌─────────┐     ┌───────────┐     ┌────────┐
│ PENDING │────▶│ COMPLETED │     │ FAILED │
└─────────┘     └───────────┘     └────────┘
     │                                 ▲
     └─────────────────────────────────┘
```

- **PENDING**: Transaction created, awaiting processing
- **COMPLETED**: Successfully processed
- **FAILED**: Processing failed

## ⚡ Key Features

### Idempotent Transaction Creation

Provide an `idempotency_key` to prevent duplicate transactions:

```json
{
  "user_id": "uuid",
  "amount": 100.00,
  "source_currency": "USD",
  "target_currency": "INR",
  "idempotency_key": "unique-client-key-123"
}
```

If a transaction with the same key exists, the existing transaction is returned.

### Clean Architecture

- **Routes**: HTTP handling only, no business logic
- **Services**: All business logic, validation, and data access
- **Models**: Database schema definitions
- **Schemas**: Request/response validation with Pydantic

## ⚠️ Limitations

This is a **demo project** with intentional limitations:

1. **Static FX Rates** - Hardcoded, not from a real provider
2. **No Real Payments** - No actual money movement
3. **Simple Auth** - Static API key, not production-grade
4. **SQLite Default** - Single-file database, not distributed
5. **No Compliance** - Not PCI-DSS or banking compliant

## 🔮 Future Improvements

- [ ] Real FX rate provider integration (XE, Open Exchange Rates)
- [ ] Async background workers for transaction processing
- [ ] Webhook notifications for status changes
- [ ] OAuth2 / JWT authentication
- [ ] PostgreSQL with connection pooling
- [ ] Rate limiting and request throttling
- [ ] Audit logging for compliance
- [ ] Kubernetes deployment configuration

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for learning backend engineering fundamentals.**
