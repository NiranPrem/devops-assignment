from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import asyncpg
import os
import time

app = FastAPI(
    title="ShopSphere API",
    version="1.0.0"
)

DATABASE_URL = os.getenv("DATABASE_URL", "")

START_TIME = time.time()
REQUEST_COUNT = 0
REQUEST_ERRORS = 0


class Customer(BaseModel):
    fullname: str
    email: str


@app.on_event("startup")
async def startup():

    app.state.db = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5
    )

    async with app.state.db.acquire() as conn:

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            category TEXT NOT NULL
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)

        await conn.execute("""
        INSERT INTO products(name,price,category)
        SELECT 'Premium Smartphone',999,'Electronics'
        WHERE NOT EXISTS (
            SELECT 1 FROM products
            WHERE name='Premium Smartphone'
        )
        """)

        await conn.execute("""
        INSERT INTO products(name,price,category)
        SELECT 'Gaming Laptop',1499,'Computers'
        WHERE NOT EXISTS (
            SELECT 1 FROM products
            WHERE name='Gaming Laptop'
        )
        """)

        await conn.execute("""
        INSERT INTO products(name,price,category)
        SELECT 'Wireless Earbuds',199,'Accessories'
        WHERE NOT EXISTS (
            SELECT 1 FROM products
            WHERE name='Wireless Earbuds'
        )
        """)

        await conn.execute("""
        INSERT INTO products(name,price,category)
        SELECT 'Smart Watch',299,'Wearables'
        WHERE NOT EXISTS (
            SELECT 1 FROM products
            WHERE name='Smart Watch'
        )
        """)


@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()


@app.get("/")
async def root():
    return {
        "application": "ShopSphere",
        "frontend": "NodeJS",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "status": "running"
    }


@app.get("/healthz")
async def healthz():
    try:

        async with app.state.db.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "uptime_seconds": round(
                time.time() - START_TIME,
                2
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():

    uptime = round(
        time.time() - START_TIME,
        2
    )

    return (
        f"# HELP app_uptime_seconds API uptime\n"
        f"# TYPE app_uptime_seconds gauge\n"
        f"app_uptime_seconds {uptime}\n"
        f"# HELP app_requests_total Total API requests\n"
        f"# TYPE app_requests_total counter\n"
        f"app_requests_total {REQUEST_COUNT}\n"
        f"# HELP app_request_errors_total Total API errors\n"
        f"# TYPE app_request_errors_total counter\n"
        f"app_request_errors_total {REQUEST_ERRORS}\n"
    )


@app.get("/products")
async def products():

    global REQUEST_COUNT
    REQUEST_COUNT += 1

    async with app.state.db.acquire() as conn:

        rows = await conn.fetch("""
        SELECT id,name,price,category
        FROM products
        ORDER BY id
        """)

        return [dict(r) for r in rows]


@app.post("/customers/register")
async def register_customer(customer: Customer):

    async with app.state.db.acquire() as conn:

        row = await conn.fetchrow(
            """
            INSERT INTO customers(fullname,email)
            VALUES($1,$2)
            RETURNING id,fullname,email,created_at
            """,
            customer.fullname,
            customer.email
        )

        return dict(row)


@app.get("/customers/list")
async def customer_list():

    async with app.state.db.acquire() as conn:

        rows = await conn.fetch("""
        SELECT id,fullname,email,created_at
        FROM customers
        ORDER BY id DESC
        """)

        return [dict(r) for r in rows]


@app.get("/customers")
async def customers():
    return {
        "total_customers": 100000,
        "active_customers": 85432,
        "premium_members": 12000
    }


@app.get("/orders")
async def orders():
    return {
        "total_orders": 50231,
        "pending_orders": 134,
        "completed_orders": 50097
    }


@app.get("/platform")
async def platform():
    return {
        "frontend": "NodeJS",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "orchestration": "Kubernetes",
        "monitoring": [
            "Prometheus",
            "Grafana",
            "Loki"
        ],
        "security": "Trivy"
    }


@app.get("/items")
async def list_items():

    async with app.state.db.acquire() as conn:

        rows = await conn.fetch("""
        SELECT id,name,created_at
        FROM items
        ORDER BY id
        """)

        return [dict(r) for r in rows]


@app.post("/items")
async def create_item(name: str):

    async with app.state.db.acquire() as conn:

        row = await conn.fetchrow(
            """
            INSERT INTO items(name)
            VALUES($1)
            RETURNING id,name,created_at
            """,
            name
        )

        return dict(row)
