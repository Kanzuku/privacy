# ME — The Life Game | Deployment Guide
## From zero to production

---

## Prerequisites

- Docker Desktop ≥ 4.x
- Node.js ≥ 20
- Python ≥ 3.12
- Expo CLI (`npm install -g expo-cli eas-cli`)
- PostgreSQL client (`psql`) for manual ops
- An Anthropic or OpenAI API key

---

## Part 1 — Local Development

### 1.1 Clone and configure

```bash
git clone https://github.com/your-org/me-life-game.git
cd me-life-game

cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and SECRET_KEY at minimum
```

### 1.2 Start all backend services

```bash
docker compose up -d postgres redis
# Wait for healthchecks (≈15s)

docker compose up -d api worker beat
```

API is live at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

### 1.3 Verify

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}

curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234"}'
# → {"access_token":"...","refresh_token":"..."}
```

### 1.4 Start the mobile frontend

```bash
cd frontend
npm install
npx expo start
# Press 'i' for iOS simulator, 'a' for Android, 'w' for web
```

---

## Part 2 — Database Migrations

Use Alembic for all schema changes. Never edit the DB directly.

```bash
# Initialize (first time only — already done in this repo)
cd me-life-game
alembic init alembic

# Create a new migration after model changes
alembic revision --autogenerate -m "add user memory table"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# View migration history
alembic history
```

**alembic/env.py** — set the database URL:
```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))
```

---

## Part 3 — Production Deployment (Railway / Render / AWS)

### Option A — Railway (recommended for MVP)

1. Push repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add services: PostgreSQL plugin, Redis plugin
4. Set environment variables (copy from .env.example)
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Deploy — Railway auto-detects Python, runs pip install

**Celery worker** — add a second Railway service from same repo:
- Start command: `celery -A app.worker worker --loglevel=info`
- Same env vars

### Option B — AWS (ECS + RDS for scale)

```
VPC
├── Public subnet
│   └── ALB (Application Load Balancer)
└── Private subnets
    ├── ECS Fargate — API service (min 2 tasks)
    ├── ECS Fargate — Celery worker (min 1 task)
    ├── RDS PostgreSQL 16 (Multi-AZ)
    └── ElastiCache Redis (cluster mode)
```

**Terraform** or **CDK** recommended for infra as code.

Key settings:
- API task: 512 MB RAM, 0.25 vCPU minimum; auto-scale at 70% CPU
- Worker task: 1 GB RAM, 0.5 vCPU (AI calls are memory-hungry)
- RDS: db.t4g.medium for MVP, upgrade to db.r6g for >10k users
- Enable RDS Performance Insights from day 1

### Option C — Docker Compose on a VPS (cheapest)

```bash
# On a fresh Ubuntu 24.04 VPS (DigitalOcean, Hetzner, etc.)
apt update && apt install -y docker.io docker-compose-plugin nginx certbot

# Copy files
scp -r . user@your-vps:/opt/me-game

# On the VPS
cd /opt/me-game
cp .env.example .env && nano .env   # set production values
ENV=production docker compose up -d

# Nginx reverse proxy
cat > /etc/nginx/sites-available/me-game << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/me-game /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL
certbot --nginx -d api.yourdomain.com
```

---

## Part 4 — Mobile App Deployment

### 4.1 Configure EAS Build

```bash
cd frontend
eas build:configure
```

**eas.json**:
```json
{
  "build": {
    "production": {
      "env": {
        "EXPO_PUBLIC_API_URL": "https://api.yourdomain.com/api/v1"
      }
    }
  }
}
```

### 4.2 Build and submit

```bash
# iOS (requires Apple Developer account)
eas build --platform ios --profile production
eas submit --platform ios

# Android (requires Google Play Console)
eas build --platform android --profile production
eas submit --platform android
```

### 4.3 OTA Updates (no app store re-review)

```bash
# Push JS-only updates instantly to all users
eas update --branch production --message "Quest system improvements"
```

---

## Part 5 — CI/CD (GitHub Actions)

**.github/workflows/deploy.yml**:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  deploy-api:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        run: |
          curl -fsSL https://railway.app/install.sh | sh
          railway up --service api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-mobile:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
        working-directory: frontend
      - run: npx eas-cli update --branch production --message "Deploy ${{ github.sha }}"
        working-directory: frontend
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
```

---

## Part 6 — Monitoring and Observability

### Sentry (error tracking)

```python
# app/main.py — already wired if SENTRY_DSN is set
import sentry_sdk
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
```

### Key metrics to track (Grafana + Prometheus or Datadog)

| Metric | Alert threshold |
|--------|----------------|
| API p95 latency | > 2000ms |
| AI engine latency | > 8000ms |
| Error rate | > 1% |
| Celery queue depth | > 100 tasks |
| DB connection pool | > 80% utilized |
| Redis memory | > 70% used |

### Scheduled jobs (Celery Beat)

```python
# app/worker.py
CELERY_BEAT_SCHEDULE = {
    # Expire daily quests at midnight
    'expire-daily-quests': {
        'task': 'app.tasks.expire_quests',
        'schedule': crontab(hour=0, minute=0),
    },
    # Update streaks daily
    'update-streaks': {
        'task': 'app.tasks.update_streaks',
        'schedule': crontab(hour=0, minute=5),
    },
    # Snapshot stat history daily
    'snapshot-stats': {
        'task': 'app.tasks.snapshot_all_stats',
        'schedule': crontab(hour=1, minute=0),
    },
    # Generate random event for active users
    'generate-events': {
        'task': 'app.tasks.generate_random_events',
        'schedule': crontab(hour=9, minute=0),   # 9am user local time (use user TZ)
    },
}
```

---

## Part 7 — Scaling Milestones

| Users | Infrastructure | Monthly cost (est.) |
|-------|---------------|---------------------|
| 0–1k | Single VPS + Docker Compose | $20–40 |
| 1k–10k | Railway / Render managed | $100–300 |
| 10k–100k | AWS ECS + RDS + ElastiCache | $500–2000 |
| 100k+ | ECS auto-scale, Aurora, CDN, read replicas | $3000+ |

**LLM cost estimate** (Anthropic claude-opus-4-5):
- Per decision simulation: ~3000 tokens in + ~2000 out ≈ $0.07
- Per quest generation: ~1500 tokens in + ~1500 out ≈ $0.04
- Per future simulation: ~2000 tokens in + ~4000 out ≈ $0.14

With 1000 DAU doing 1 decision + 1 quest gen/day: ~$110/day → add to pricing accordingly.

---

## Part 8 — Security Checklist for Production

- [ ] Rotate `SECRET_KEY` and store in AWS Secrets Manager / Railway secrets
- [ ] Enable RDS encryption at rest
- [ ] Set `docs_url=None` in production FastAPI (already wired)
- [ ] Rate limit AI endpoints: max 10 decision simulations/user/day on free tier
- [ ] Validate all user inputs with Pydantic (already enforced by schema)
- [ ] Set CORS to specific production domains only
- [ ] Enable CloudFlare WAF in front of API
- [ ] Rotate API keys quarterly
- [ ] Audit log all decision simulations (GDPR compliance)
- [ ] Implement data deletion endpoint for GDPR right-to-erasure

---

*ME — The Life Game | Production-ready MVP v1.0*
