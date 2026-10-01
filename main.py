"""Time Capsule API - Messages that reveal at a future date"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3, secrets

app = FastAPI(title="Time Capsule API")

def db():
    conn = sqlite3.connect("capsules.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS capsules (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        unlock_at TEXT NOT NULL
    )""")  # ponytail: removed created_at, not needed yet
    return conn

class Capsule(BaseModel):
    content: str
    unlock_at: datetime

@app.post("/capsules")
def create(c: Capsule):
    if c.unlock_at <= datetime.utcnow():
        raise HTTPException(400, "unlock_at must be in the future")
    id = secrets.token_urlsafe(8)
    with db() as conn:
        conn.execute("INSERT INTO capsules VALUES (?,?,?)", (id, c.content, c.unlock_at.isoformat()))
    return {"id": id, "unlocks_at": c.unlock_at, "url": f"/capsules/{id}"}

@app.get("/capsules/{id}")
def get(id: str):
    with db() as conn:
        row = conn.execute("SELECT content, unlock_at FROM capsules WHERE id=?", (id,)).fetchone()
    if not row:
        raise HTTPException(404, "Not found")
    unlock = datetime.fromisoformat(row[1])
    if datetime.utcnow() < unlock:
        delta = unlock - datetime.utcnow()
        raise HTTPException(403, f"🔒 Opens in {delta.days}d {delta.seconds//3600}h {(delta.seconds%3600)//60}m")
    return {"content": row[0], "unlocked_at": row[1]}

@app.get("/capsules/{id}/status")
def status(id: str):
    with db() as conn:
        row = conn.execute("SELECT unlock_at FROM capsules WHERE id=?", (id,)).fetchone()
    if not row:
        raise HTTPException(404)
    unlock = datetime.fromisoformat(row[0])
    now = datetime.utcnow()
    locked = now < unlock
    return {"locked": locked, "unlock_at": row[0], "remaining": str(unlock - now).split('.')[0] if locked else None}

if __name__ == "__main__":
    from datetime import timedelta
    print("=== Demo ===")
    c = Capsule(content="Hello future me!", unlock_at=datetime.utcnow() + timedelta(seconds=2))
    r = create(c)
    print(f"Created: {r['id']}")
    print(f"Status: {status(r['id'])}")
    import time; time.sleep(3)
    print(f"Content: {get(r['id'])}")
