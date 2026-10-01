"""Time Capsule API"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3, secrets, os

app = FastAPI(title="Time Capsule API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "/tmp/capsules.db" if os.getenv("VERCEL") else "capsules.db"

def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS capsules (id TEXT PRIMARY KEY, content TEXT, unlock_at TEXT)")
    return conn

class Capsule(BaseModel):
    content: str
    unlock_at: datetime

@app.get("/")
def root():
    return {"api": "Time Capsule", "docs": "/docs"}

@app.post("/capsules")
def create(c: Capsule):
    if c.unlock_at <= datetime.utcnow():
        raise HTTPException(400, "unlock_at must be future")
    id = secrets.token_urlsafe(8)
    with db() as conn:
        conn.execute("INSERT INTO capsules VALUES (?,?,?)", (id, c.content, c.unlock_at.isoformat()))
    return {"id": id, "unlocks_at": c.unlock_at}

@app.get("/capsules/{id}")
def get(id: str):
    with db() as conn:
        row = conn.execute("SELECT content, unlock_at FROM capsules WHERE id=?", (id,)).fetchone()
    if not row: raise HTTPException(404)
    unlock = datetime.fromisoformat(row[1])
    if datetime.utcnow() < unlock:
        d = unlock - datetime.utcnow()
        raise HTTPException(403, f"🔒 {d.days}d {d.seconds//3600}h {(d.seconds%3600)//60}m remaining")
    return {"content": row[0]}

@app.get("/capsules/{id}/status")
def status(id: str):
    with db() as conn:
        row = conn.execute("SELECT unlock_at FROM capsules WHERE id=?", (id,)).fetchone()
    if not row: raise HTTPException(404)
    unlock = datetime.fromisoformat(row[0])
    locked = datetime.utcnow() < unlock
    return {"locked": locked, "unlock_at": row[0]}
