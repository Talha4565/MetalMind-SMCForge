# Pipeline Orchestrator Test Report

## Date: June 16, 2026

### Test Results

| Feature | Status | Details |
|---------|--------|---------|
| Data Freshness Check | PASS | Detects stale data (41.6h old, max 25h) |
| Model Versioning | PASS | Creates backup (1.18 MB), lists backups |
| Health Monitoring | PASS | Records update/retrain success, persists to JSON |
| Pipeline Status | PASS | Full dashboard data with health, freshness, backups |

### Data Freshness
- Gold: STALE (41.6h old, max 25h) — 469,263 rows
- Silver: STALE (41.6h old, max 25h) — 216,662 rows

### Model Versioning
- Backup created: gold_model_20260616_173549.pkl (1.18 MB)
- Keeps last 5 backups per asset
- Auto-rollback on retrain failure

### Health Monitoring
- Tracks update/retrain success/failure
- Alerts after 3 consecutive failures
- Persists to reports/pipeline_health.json

### Pipeline Status
- Shows health (healthy/degraded/critical)
- Tracks job status (running/success/failed)
- API endpoint: GET /api/pipeline/status
