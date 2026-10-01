# ⏰ Time Capsule API

Messages that reveal at a future date. Returns 403 until unlock time.

## Endpoints

```
POST /capsules          Create locked message
GET  /capsules/{id}     403 until unlock, then content
GET  /capsules/{id}/status   Check countdown
GET  /docs              Swagger UI
```

## Usage

```bash
# Create capsule (unlocks in 1 hour)
curl -X POST https://time-capsule-api.vercel.app/capsules \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello future!", "unlock_at": "2027-01-01T00:00:00"}'

# Try to read (403 if locked)
curl https://time-capsule-api.vercel.app/capsules/{id}

# Check status
curl https://time-capsule-api.vercel.app/capsules/{id}/status
```

## Stack

FastAPI + SQLite. 45 lines.

## Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Naell-Kopling/time-capsule-api)
