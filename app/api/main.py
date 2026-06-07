from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import asyncpg
import os
import time

app = FastAPI(title="DevOps Assignment API", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL", "")
PORT = int(os.getenv("PORT", "8000"))

START_TIME = time.time()
REQUEST_COUNT = 0
REQUEST_ERRORS = 0


@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with app.state.db.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()


@app.get("/healthz")
async def healthz():
    try:
        async with app.state.db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "uptime": round(time.time() - START_TIME, 2)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    uptime = round(time.time() - START_TIME, 2)
    return (
        f"# HELP app_uptime_seconds Uptime of the API service\n"
        f"# TYPE app_uptime_seconds gauge\n"
        f"app_uptime_seconds {uptime}\n"
        f"# HELP app_requests_total Total HTTP requests\n"
        f"# TYPE app_requests_total counter\n"
        f"app_requests_total {REQUEST_COUNT}\n"
        f"# HELP app_request_errors_total Total request errors\n"
        f"# TYPE app_request_errors_total counter\n"
        f"app_request_errors_total {REQUEST_ERRORS}\n"
    )


@app.get("/items")
async def list_items():
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, created_at FROM items ORDER BY id")
        return [dict(r) for r in rows]


@app.post("/items")
async def create_item(name: str):
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    async with app.state.db.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO items (name) VALUES ($1) RETURNING id, name, created_at", name
        )
        return dict(row)
