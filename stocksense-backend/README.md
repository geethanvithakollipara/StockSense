# StockSense — Inventory Management System (Backend API)

A modular Flask + SQLite REST API implementing the StockSense problem
statement: authentication, dashboard KPIs, product management, receipts
(incoming stock), delivery orders (outgoing stock), internal transfers,
stock adjustments, move history (stock ledger), and warehouse settings.

No external database server is required — it runs on SQLite out of the box.

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit SECRET_KEY etc. as needed
python run.py                   # starts on http://localhost:5000
```

The database file is created automatically at `instance/stocksense.db`
the first time the app runs. Optionally seed some starter data:

```bash
python seed.py
```

## 2. Authentication

All endpoints except `/api/auth/*` and `/api/health` require a JWT sent as:

```
Authorization: Bearer <token>
```

`token` is returned by `/api/auth/signup` or `/api/auth/login`.

| Method | Endpoint                     | Description                                   |
|--------|-------------------------------|------------------------------------------------|
| POST   | /api/auth/signup              | Create an account (`name`, `email`, `password`, `role`) |
| POST   | /api/auth/login                | Log in, returns JWT + redirect to dashboard    |
| POST   | /api/auth/forgot-password      | Generate an OTP for password reset             |
| POST   | /api/auth/reset-password       | Verify OTP + set a new password                |
| GET    | /api/auth/me                   | Current authenticated user                     |

> OTP delivery: in this reference implementation the OTP is generated and
> stored server-side (10 min expiry). Plug in a real SMS/email provider in
> `app/routes/auth.py::forgot_password` for production; while `FLASK_DEBUG`
> is on, the OTP is also returned in the response for local testing.

## 3. Dashboard

| Method | Endpoint               | Description |
|--------|------------------------|-------------|
| GET    | /api/dashboard/kpis     | Total products, low/out-of-stock counts, pending receipts/deliveries/transfers |
| GET    | /api/dashboard/documents?doc_type=&status=&warehouse_id=&category_id= | Dynamic filtering across any document type |

## 4. Products

| Method | Endpoint                          | Description |
|--------|------------------------------------|-------------|
| GET    | /api/products?search=&category_id=&warehouse_id=&low_stock=true | List / search / filter products |
| POST   | /api/products                      | Create product (`name`, `sku`, `category_id`, `uom`, `reorder_min`, `reorder_max`, optional `initial_stock`) |
| GET    | /api/products/:id                  | Product detail incl. per-location stock |
| PUT    | /api/products/:id                  | Update product |
| DELETE | /api/products/:id                  | Delete product (blocked if it still has stock) |
| GET    | /api/products/:id/stock             | Stock availability per warehouse/location |
| GET/POST | /api/categories                  | List / create product categories |

## 5. Settings

| Method | Endpoint                | Description |
|--------|--------------------------|-------------|
| GET/POST | /api/warehouses         | List / create warehouses (also used for racks/sub-locations) |
| PUT/DELETE | /api/warehouses/:id    | Update / delete a warehouse |
| GET/POST | /api/suppliers          | List / create suppliers |

## 6. Receipts — Incoming Stock

| Method | Endpoint                       | Description |
|--------|---------------------------------|-------------|
| GET    | /api/receipts?status=&warehouse_id=&category_id= | List receipts |
| POST   | /api/receipts                   | Create receipt: `{ warehouse_id, supplier_id, lines: [{product_id, expected_qty}], notes }` |
| GET    | /api/receipts/:id                | Receipt detail |
| PUT    | /api/receipts/:id                | Edit quantities before validation |
| POST   | /api/receipts/:id/validate        | Validate → stock **increases** automatically |
| POST   | /api/receipts/:id/cancel          | Cancel a draft/waiting receipt |

## 7. Delivery Orders — Outgoing Stock

| Method | Endpoint                        | Description |
|--------|----------------------------------|-------------|
| GET    | /api/deliveries?status=&warehouse_id=&category_id() | List delivery orders |
| POST   | /api/deliveries                  | Create: `{ warehouse_id, customer_name, lines: [{product_id, expected_qty}], notes }` |
| GET    | /api/deliveries/:id               | Delivery detail |
| POST   | /api/deliveries/:id/pick           | Mark items picked (waiting → ready) |
| POST   | /api/deliveries/:id/validate       | Pack + validate → stock **decreases** automatically (blocked if insufficient stock) |
| POST   | /api/deliveries/:id/cancel         | Cancel a draft/waiting/ready delivery |

## 8. Internal Transfers

| Method | Endpoint                       | Description |
|--------|----------------------------------|-------------|
| GET    | /api/transfers?status=&warehouse_id=&category_id= | List transfers |
| POST   | /api/transfers                   | Create: `{ source_warehouse_id, dest_warehouse_id, lines: [{product_id, expected_qty}], notes }` |
| GET    | /api/transfers/:id                | Transfer detail |
| POST   | /api/transfers/:id/validate        | Validate → total stock unchanged, location updated; logged at both ends |
| POST   | /api/transfers/:id/cancel          | Cancel a pending transfer |

> Model racks/sub-locations (e.g. "Rack A", "Rack B") simply as additional
> `warehouses` rows so the same transfer logic covers Main Warehouse ↔
> Production Floor and Rack A ↔ Rack B alike.

## 9. Stock Adjustments

| Method | Endpoint                        | Description |
|--------|-----------------------------------|-------------|
| GET    | /api/adjustments?status=&warehouse_id=&category_id= | List adjustments |
| POST   | /api/adjustments                  | Create: `{ warehouse_id, lines: [{product_id, counted_qty}], notes }` — system records the currently recorded quantity per line automatically |
| GET    | /api/adjustments/:id               | Adjustment detail |
| POST   | /api/adjustments/:id/validate       | System auto-updates stock to the counted quantity and logs the delta |
| POST   | /api/adjustments/:id/cancel         | Cancel a pending adjustment |

## 10. Move History (Stock Ledger)

| Method | Endpoint                                                            | Description |
|--------|-----------------------------------------------------------------------|-------------|
| GET    | /api/move-history?product_id=&warehouse_id=&doc_type=&date_from=&date_to= | Full audit trail of every stock movement |

## 11. Profile

| Method | Endpoint                       | Description |
|--------|-----------------------------------|-------------|
| GET    | /api/profile                     | Current user profile |
| PUT    | /api/profile                      | Update name |
| POST   | /api/profile/change-password      | Change password |

## 12. Example flow (matches the spec's worked example)

```bash
# 1. Sign up and log in
curl -X POST localhost:5000/api/auth/signup -H "Content-Type: application/json" \
  -d '{"name":"Asha","email":"asha@example.com","password":"secret123"}'

TOKEN=<paste token from response>

# 2. Create warehouses
curl -X POST localhost:5000/api/warehouses -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"name":"Main Store"}'
curl -X POST localhost:5000/api/warehouses -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"name":"Production Rack"}'

# 3. Create a product
curl -X POST localhost:5000/api/products -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Steel Rods","sku":"STL-001","uom":"kg","reorder_min":10}'

# 4. Receive 100 kg steel -> Main Store   (Step 1)
curl -X POST localhost:5000/api/receipts -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":1,"lines":[{"product_id":1,"expected_qty":100}]}'
curl -X POST localhost:5000/api/receipts/1/validate -H "Authorization: Bearer $TOKEN"

# 5. Internal transfer Main Store -> Production Rack   (Step 2)
curl -X POST localhost:5000/api/transfers -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_warehouse_id":1,"dest_warehouse_id":2,"lines":[{"product_id":1,"expected_qty":100}]}'
curl -X POST localhost:5000/api/transfers/1/validate -H "Authorization: Bearer $TOKEN"

# 6. Deliver 20 kg finished steel from Production Rack   (Step 3)
curl -X POST localhost:5000/api/deliveries -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":2,"lines":[{"product_id":1,"expected_qty":20}]}'
curl -X POST localhost:5000/api/deliveries/1/validate -H "Authorization: Bearer $TOKEN"

# 7. Adjust for 3 kg damaged   (Step 4)
curl -X POST localhost:5000/api/adjustments -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":2,"lines":[{"product_id":1,"counted_qty":77}]}'
curl -X POST localhost:5000/api/adjustments/1/validate -H "Authorization: Bearer $TOKEN"

# 8. See everything logged in the Stock Ledger
curl localhost:5000/api/move-history -H "Authorization: Bearer $TOKEN"
```

Final expected balance: Production Rack ends at 77 kg (100 received → 100
moved in → 20 delivered → 3 adjusted off = 77), matching the spec's example.

## 13. Project structure

```
stocksense-backend/
├── run.py                 # entry point
├── seed.py                # optional demo data
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py         # Flask app factory + blueprint registration
    ├── database.py         # SQLite connection helpers
    ├── schema.sql           # full DB schema
    ├── routes/
    │   ├── auth.py
    │   ├── products.py
    │   ├── settings.py       # warehouses / categories / suppliers
    │   ├── receipts.py
    │   ├── deliveries.py
    │   ├── transfers.py
    │   ├── adjustments.py
    │   ├── move_history.py
    │   ├── dashboard.py
    │   └── profile.py
    └── utils/
        ├── security.py       # password hashing, JWT, @login_required
        ├── inventory.py       # stock mutation + ledger logging
        └── documents.py       # shared document CRUD/list helpers
```

## 14. Notes on production hardening

- Swap SQLite for PostgreSQL by replacing `app/database.py` (schema is
  standard SQL and translates directly).
- Wire `forgot_password` to a real SMS/email provider and remove the
  `debug_otp` field.
- Add rate limiting on `/api/auth/*`.
- Set a strong, random `SECRET_KEY` in `.env` and disable `FLASK_DEBUG`.
