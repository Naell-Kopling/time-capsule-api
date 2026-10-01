"""Time Capsule API"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3, secrets, os

app = FastAPI(title="Time Capsule API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB = "/tmp/capsules.db" if os.getenv("VERCEL") else "capsules.db"

def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS capsules (id TEXT PRIMARY KEY, content TEXT, unlock_at TEXT)")
    return conn

class Capsule(BaseModel):
    content: str
    unlock_at: datetime

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Time Capsule</title>
  <link rel="icon" href="https://naell-portofolio.vercel.app/favicon.png">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root{--bg:#0a0a0a;--card:#111;--text:#f5f5f5;--dim:#777;--accent:#e63946;--border:#222}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 20px}
    .logo{height:32px;margin-bottom:32px}
    h1{font-size:clamp(32px,6vw,48px);font-weight:700;letter-spacing:-2px;margin-bottom:8px}
    h1 span{color:var(--accent)}
    .sub{color:var(--dim);margin-bottom:40px;font-size:14px}
    .card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px;width:100%;max-width:400px;margin-bottom:20px}
    .card h2{font-size:16px;margin-bottom:16px}
    label{display:block;font-size:12px;color:var(--dim);margin-bottom:6px}
    textarea,input{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:12px;color:var(--text);font-size:14px;margin-bottom:16px;resize:none}
    textarea:focus,input:focus{outline:none;border-color:var(--accent)}
    button{width:100%;padding:14px;background:var(--accent);color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:transform .2s}
    button:hover{transform:translateY(-2px)}
    button:disabled{opacity:0.5;cursor:not-allowed}
    .result{background:rgba(230,57,70,.1);border:1px solid rgba(230,57,70,.3);border-radius:10px;padding:16px;font-size:13px;word-break:break-all;margin-top:16px}
    .msg{padding:16px;border-radius:10px;font-size:14px;margin-top:16px}
    .msg.locked{background:rgba(230,57,70,.1);color:var(--accent)}
    .msg.unlocked{background:rgba(34,197,94,.1);color:#22c55e}
    .msg.error{background:rgba(230,57,70,.1);color:var(--accent)}
    .footer{margin-top:auto;padding-top:40px;font-size:12px;color:var(--dim)}
    .footer a{color:var(--accent);text-decoration:none}
  </style>
</head>
<body>
  <img src="https://naell-portofolio.vercel.app/logo.png" alt="L" class="logo">
  <h1>Time Capsule<span>.</span></h1>
  <p class="sub">Messages that reveal at a future date</p>
  <div class="card">
    <h2>📦 Create Capsule</h2>
    <label>Message</label>
    <textarea id="content" rows="3" placeholder="Dear future me..."></textarea>
    <label>Unlock Date & Time</label>
    <input type="datetime-local" id="unlock">
    <button id="lockBtn" onclick="create()">Lock It 🔒</button>
    <div id="create-result"></div>
  </div>
  <div class="card">
    <h2>🔓 Open Capsule</h2>
    <input type="text" id="capsule-id" placeholder="Capsule ID">
    <button onclick="openCapsule()">Open</button>
    <div id="open-result"></div>
  </div>
  <p class="footer">by <a href="https://naell-portofolio.vercel.app">Leonardo</a> · <a href="https://github.com/Naell-Kopling/time-capsule-api">GitHub</a></p>
  <script>
    async function create(){
      const content = document.getElementById('content').value;
      const unlock = document.getElementById('unlock').value;
      const btn = document.getElementById('lockBtn');
      const result = document.getElementById('create-result');
      
      if(!content || !unlock) {
        result.innerHTML = '<div class="msg error">⚠️ Fill message and date</div>';
        return;
      }
      
      btn.disabled = true;
      btn.textContent = 'Creating...';
      
      try {
        const unlockDate = new Date(unlock);
        const res = await fetch('/capsules', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({content, unlock_at: unlockDate.toISOString()})
        });
        const data = await res.json();
        
        if(res.ok) {
          result.innerHTML = '<div class="result">✅ Capsule Created!<br><br><b>ID:</b> ' + data.id + '<br><b>Unlocks:</b> ' + new Date(data.unlocks_at).toLocaleString() + '</div>';
          document.getElementById('content').value = '';
        } else {
          result.innerHTML = '<div class="msg error">❌ ' + (data.detail || 'Error') + '</div>';
        }
      } catch(e) {
        result.innerHTML = '<div class="msg error">❌ Network error: ' + e.message + '</div>';
      }
      
      btn.disabled = false;
      btn.textContent = 'Lock It 🔒';
    }
    
    async function openCapsule(){
      const id = document.getElementById('capsule-id').value.trim();
      const result = document.getElementById('open-result');
      if(!id) {
        result.innerHTML = '<div class="msg error">⚠️ Enter capsule ID</div>';
        return;
      }
      
      try {
        const res = await fetch('/capsules/' + id);
        const data = await res.json();
        
        if(res.status === 403) {
          result.innerHTML = '<div class="msg locked">' + data.detail + '</div>';
        } else if(res.ok) {
          result.innerHTML = '<div class="msg unlocked">🎉 <b>Message:</b><br><br>' + data.content + '</div>';
        } else {
          result.innerHTML = '<div class="msg error">❌ Capsule not found</div>';
        }
      } catch(e) {
        result.innerHTML = '<div class="msg error">❌ Network error</div>';
      }
    }
    
    // Set default to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('unlock').value = tomorrow.toISOString().slice(0,16);
    document.getElementById('unlock').min = new Date().toISOString().slice(0,16);
  </script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.post("/capsules")
def create(c: Capsule):
    if c.unlock_at <= datetime.utcnow():
        raise HTTPException(400, "Date must be in the future")
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
    return {"locked": datetime.utcnow() < datetime.fromisoformat(row[0]), "unlock_at": row[0]}
