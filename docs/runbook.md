# Fraud Agentic AI — Operations Runbook

## Quick Commands

```bash
make dev          # Start all services locally
make test         # Run all tests
make eval         # Run LLM evaluation suite
make docker-up    # Docker Compose up
make docker-down  # Docker Compose down
make seed-db      # Seed ChromaDB with fraud cases
make smoke-test   # Smoke test MCP servers
```

## Service Ports

| Service | Port |
|---|---|
| FastAPI | 8000 |
| Banking MCP Server | 8002 |
| Compliance MCP Server | 8003 |
| Redis | 6379 |
| ChromaDB | 8001 |
| Prometheus | 9090 |
| Grafana | 3000 |

## Health Checks

```bash
# Full stack health
curl http://localhost:8000/health

# Banking MCP
curl http://localhost:8002/health

# Compliance MCP
curl http://localhost:8003/health

# Redis
redis-cli ping
```

## Common Issues

### Agents returning low-confidence outputs
- Check LangSmith traces for token limit issues
- Verify OpenAI API key is valid
- Check `OPENAI_MODEL` env var — must be `gpt-4o`

### Redis connection failures
- `docker compose restart redis`
- Check `REDIS_URL` in `.env`
- Sessions will re-create on next request (no data loss for new transactions)

### ChromaDB empty results
- Run `make seed-db` to reload fraud cases
- Check `CHROMA_HOST` and `CHROMA_PORT` in `.env`

### MCP tool call failures
- Check Banking MCP logs: `docker compose logs banking-mcp`
- Check Compliance MCP logs: `docker compose logs compliance-mcp`
- Tool failures are non-fatal — agents continue with partial data

### Rate limit errors (429)
- Default: 60 req/min per IP
- Adjust `RATE_LIMIT_PER_MINUTE` in `.env`
- Redis key: `rate_limit:{ip}` (expires after 60s)

## Deployment (AKS)

```bash
# Deploy via Helm
helm upgrade --install fraud-agentic-ai ./helm \
  --namespace fraud-ai \
  --set image.tag=1.0.0 \
  --set env.OPENAI_API_KEY=$OPENAI_API_KEY

# Rollback
helm rollback fraud-agentic-ai -n fraud-ai

# Check pods
kubectl get pods -n fraud-ai
kubectl logs -f deployment/fraud-agentic-ai -n fraud-ai
```

## Incident Response

### P1: Auto-block triggering incorrectly
1. Check LangSmith traces for the transaction session
2. Review `audit.log` for the `audit_trail_id`
3. Manual override via `POST /api/v1/escalate` with `risk_level: LOW`
4. Notify compliance team within 1 hour

### P2: High LLM error rate
1. Check OpenAI status page
2. Temporarily switch to `gpt-4o-mini` via `OPENAI_MODEL` env var
3. LangSmith will show all failed traces

### P3: Slow agent responses (>500ms)
1. Check Redis memory usage
2. Check ChromaDB query latency in Grafana
3. Check MCP server response times in OTel dashboard
