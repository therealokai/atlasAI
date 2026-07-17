# Real Estate AI Agent — Phase 0 + Phase 1 Daily Checklist

**Pace:** ~4 focused hours/day · **Span:** 2 working weeks (10 sessions) · **Goal:** two green exit criteria, one build log

Rule for every day: don't start until you've read yesterday's build-log entry. Don't end without writing today's.

---

## Day 0 (before Day 1 — 15 min sanity check)
- [x] `nvidia-smi` confirms the L40S is visible and drivers are healthy
- [x] `docker --version` and `docker compose version` both work
- [x] Create the build log file now: `docs/build-log.md` — one entry per day, 3 lines max: *did / broke / next question*

---

## PHASE 0 — Foundations

### Day 1 — Repo skeleton + compose scaffold (infra only, no app code)
- [x] Create monorepo layout: `services/{gateway,router,worker}/`, `mcp/`, `deploy/`, `experiments/`, `eval/`, `docs/`
- [x] Write `docker-compose.yml` with just **Postgres, Qdrant, Redis** (no app services yet — vLLM comes Day 6)
- [x] `docker compose up` → confirm all three containers start and stay up
- [x] Add a `.env.example` with placeholder connection strings
- [x] Build log entry

### Day 2 — Seed data
- [x] Write Postgres schema: `units`, `conversations` tables (minimal columns — you'll extend in Phase 2)
- [x] Write a synthetic-data generator: 500–2,000 fake real-estate units (city, price, beds, type)
- [x] Load 20–50 sample "documents" (can be plain text stand-ins for brochures/payment plans for now — real chunking is Phase 2)
- [x] Verify via `psql`: `SELECT count(*) FROM units;` returns expected count
- [x] Build log entry

### Day 3 — CI + observability skeleton
- [ ] Add CI config (GitHub Actions or similar): lint step + placeholder unit test + docker build step
- [ ] Push a trivial change and confirm CI goes green
- [ ] Add Prometheus + Grafana + OTel-collector as compose services (empty dashboards are fine — just prove they start)
- [ ] Build log entry

### Day 4 — Wire health checks + browse sanity
- [ ] Add `healthcheck:` blocks to every compose service (Postgres, Qdrant, Redis)
- [ ] `docker compose up` → `docker compose ps` shows all services `healthy`, not just `running`
- [ ] Browse seeded data in a UI: psql (or a GUI client) for Postgres, Qdrant's dashboard for the empty collections
- [ ] Build log entry

### Day 5 — Phase 0 close-out (buffer day)
- [ ] Catch up on anything slipped from Days 1–4
- [ ] Write a short **Phase 0 exit report** (5–10 lines) in `docs/`: what exists, what the exit criteria were, confirm all green
- [ ] Exit criteria check: ✅ `docker compose up` → health checks green ✅ seeded data browsable via psql/Qdrant UI
- [ ] Build log entry — explicitly write "Phase 0 done, starting Phase 1 tomorrow"

**Do not start Day 6 until Day 5's checklist is fully checked.** This is the discipline, not a formality.

---

## PHASE 1 — Serving Baseline

### Day 6 — vLLM standalone (sort out GPU issues in isolation first)
- [ ] Pick your T2 model per the design doc (e.g. Qwen2.5-14B AWQ-INT4 — fits ~10–16 GB on the L40S)
- [ ] Install vLLM and serve the model **standalone**, outside compose, just `vllm serve ...` from the CLI
- [ ] Confirm you can hit `/v1/chat/completions` directly with `curl` and get a real response
- [ ] If you hit CUDA/driver issues, this is the day to fight them — don't let compose complexity hide a GPU problem
- [ ] Build log entry

### Day 7 — Gateway + compose integration
- [ ] Add vLLM as a service in `docker-compose.yml`
- [ ] Build the tiny FastAPI gateway: `/health` (checks vLLM is reachable) + `/v1/chat` as a pure pass-through — **no router, no PII, no tools**
- [ ] Confirm end-to-end: gateway `/v1/chat` → vLLM → real response
- [ ] Build log entry

### Day 8 — Golden-set v1
- [ ] Write 100 real-estate-domain prompts in `eval/golden-set-v1.json` (mix: chit-chat, lookups, harder reasoning — even though tools/RAG aren't wired yet, the model still needs to *answer* something)
- [ ] Sanity-run 5–10 of them through the gateway manually, eyeball response quality
- [ ] Build log entry

### Day 9 — Load testing setup
- [ ] Write a k6 script that replays the golden set against `/v1/chat`
- [ ] Add Prometheus scraping of vLLM's built-in metrics endpoint
- [ ] Run k6 once at concurrency 1 just to confirm the harness works end-to-end (don't trust numbers yet — this is a plumbing check)
- [ ] Build log entry

### Day 10 — Baseline report + Phase 1 close-out
- [ ] Run k6 at concurrency **1, 4, 16, 64**
- [ ] Record p95 TTFT, TPOT, throughput at each level in `experiments/baseline-report.md`
- [ ] Compare against your SLO targets from §1.3 (p95 TTFT < 1.5s for tiny/strong tier) — just record where you stand, don't panic if you're not there yet
- [ ] Exit criteria check: ✅ baseline report exists with real numbers at all four concurrency levels
- [ ] Build log entry — this baseline number is the one you'll quote for months, so make sure it's written down somewhere durable, not just in your head

---

## After Day 10
Phase 2 (Data & Tools — Postgres/Qdrant ingest, MCP servers, agent loop) is next, per the main design doc. Don't start it until the Phase 1 exit criteria above are genuinely green — that discipline is the whole point of this exercise.
