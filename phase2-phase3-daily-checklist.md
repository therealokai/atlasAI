# Real Estate AI Agent — Phase 2 + Phase 3 Daily Checklist

**Pace:** ~4 focused hours/day · **Span:** Phase 2 = 2 weeks (10 sessions), Phase 3 = ~2.5–3 weeks (14 sessions)
**Goal:** two green exit criteria, one build log per phase, no orphan features

Rule for every day: don't start until you've read yesterday's build-log entry. Don't end without writing today's.
**Do not start Phase 3 (Day 21) until Phase 2's exit criteria (Day 20) are fully green.**

---

## PHASE 2 — Data & Tools

### Day 11 — Real Postgres schema + inventory ingest
- [ ] Extend `units` table to full schema: `type, city, district, price, bedrooms, area_m2, amenities jsonb, description, embedding_id, status`
- [ ] Add `conversations`, `messages` tables (columns per §9.1 — `tool_calls` and `routing_log` come Day 26, not yet)
- [ ] Write/adapt ingest script: replace Phase 0 synthetic units with real (or higher-fidelity synthetic) inventory
- [ ] Verify via `psql`: row counts and a few spot-check queries (filter by city/price/beds)
- [ ] Build log entry

### Day 12 — Qdrant collections + embedding sidecar
- [ ] Stand up a multilingual-e5/bge-m3-class embedding model as a small sidecar service (CPU is fine)
- [ ] Create `units_embeddings_v1` collection (versioned name — re-embedding later is a blue/green swap)
- [ ] Payload schema: city, price, type, bedrooms, area_m2 (the filterable fields)
- [ ] Build log entry

### Day 13 — Embed units, prove hybrid search works
- [ ] Embed `description + structured fields` for every unit, upsert into Qdrant
- [ ] Run one manual hybrid query (filter + vector, e.g. "family-friendly near a park" + city=X) and eyeball relevance
- [ ] Confirm filter-only queries (hard constraints like `bedrooms=4, price<15M`) return correct rows
- [ ] Build log entry

### Day 14 — Document chunking pipeline
- [ ] Create `documents_chunks` collection; payload = `{doc_id, section, page}`
- [ ] Build chunking pipeline: 300–500 tokens, 15% overlap, over the Phase 0 sample docs (or real brochures/payment plans if available)
- [ ] Embed and upsert chunks; verify a manual query returns the right chunk + correct `doc_id/page`
- [ ] Build log entry

### Day 15 — MCP `property-search` server
- [ ] Stand up as its own container, own FastAPI health endpoint, manifest at `/.well-known/mcp`
- [ ] Implement `search_units(filters, query, k)` — SQL for hard filters, vector for semantic, **merge in the tool, not the prompt**
- [ ] Implement `get_unit(id)` and `list_cities()`
- [ ] Test standalone (no agent loop yet) with a raw MCP/tool call
- [ ] Build log entry

### Day 16 — MCP `doc-qa` server
- [ ] Stand up as its own container with health endpoint + manifest
- [ ] Implement `search_docs(query, doc_type?, k)` → returns chunks **with citations** (`doc_id`, `page`)
- [ ] Test standalone: query a known payment-plan fact, confirm the right chunk + citation comes back
- [ ] Build log entry

### Day 17 — Agent loop v1 (single tool round-trip)
- [ ] Wire the worker to call the T2 model with tool manifests attached
- [ ] Implement one full round: model picks a tool → worker calls MCP tool → result fed back → model answers
- [ ] Manually test both tools this way (property search, doc-qa) — no router yet, tool choice can be hardcoded/forced for now
- [ ] Build log entry

### Day 18 — Agent loop v2 (multi-round + validity + citations)
- [ ] Extend loop to allow up to **3 model↔tool rounds** before forcing a final answer
- [ ] Enforce: doc-qa answers **must** include a citation or the answer is rejected/retried
- [ ] Add a tool-call JSON validity check (schema validation before the tool is actually invoked)
- [ ] Build log entry

### Day 19 — Golden-set v2 + functional-correctness harness
- [ ] Write 30–50 property-search prompts and 20–30 doc-qa prompts into `eval/golden-set-v2.json`
- [ ] Run the full set through the agent loop; log: tool-call JSON validity %, citation-presence % for doc-qa
- [ ] This is a **correctness check, not a performance benchmark** — no timing/quality scoring yet (that's Phase 5)
- [ ] Build log entry

### Day 20 — Phase 2 close-out
- [ ] Catch up on anything slipped from Days 11–19
- [ ] Write Phase 2 exit report: what exists, tool-call JSON validity number, example transcripts for both target queries
- [ ] Exit criteria check: ✅ "4-bed villa in New Cairo under 15M" answered from real data ✅ "what does the payment plan say" answered with citation ✅ tool-call JSON validity ≥ 98%
- [ ] Build log entry — explicitly write "Phase 2 done, starting Phase 3 tomorrow"

**Do not start Day 21 until Day 20's checklist is fully checked.**

---

## PHASE 3 — Router Stack

### Day 21 — PII synthetic data
- [ ] Generate 5–10k synthetic chat messages using the flagship model, covering Egyptian/Gulf names, phone formats, national IDs, compound addresses
- [ ] Label with BIO tags for entities: PERSON, PHONE, EMAIL, NATIONAL_ID, ADDRESS, BANK/IBAN
- [ ] Combine with a public PII dataset (e.g. `ai4privacy/pii-masking-*`) as base training data
- [ ] Decide explicitly: scrub **only personal** addresses, not property-listing addresses (business data) — write the decision down
- [ ] Build log entry

### Day 22 — PII service — fine-tune
- [ ] Fine-tune `ModernBERT-base` for token classification on the combined dataset
- [ ] Serve it ONNX/quantized on CPU (target < 10ms, keep it out of GPU budget)
- [ ] Sanity-check on 10–20 held-out examples
- [ ] Build log entry

### Day 23 — PII service — eval + release gate
- [ ] Build a held-out eval set; measure per-entity precision/recall
- [ ] **Release gate: recall ≥ 98%** — if not met, this blocks moving forward (add more synthetic data, don't skip the gate)
- [ ] Build log entry

### Day 24 — PII vault integration
- [ ] Wire the PII service into the gateway: `scrub(message)` → placeholders (`[NAME_1]`, `[PHONE_1]`...)
- [ ] Store mapping in Redis `pii:{session_id}` vault with TTL = session TTL
- [ ] Confirm: only scrubbed text ever gets logged or stored from this point forward
- [ ] Build log entry

### Day 25 — PII re-identification + end-to-end test
- [ ] Implement gateway re-ID: substitute placeholders back **only if** the model echoed them **and** the vault entry still exists; otherwise drop the placeholder
- [ ] Run a full scrub → model → re-ID round trip manually and confirm correctness
- [ ] Build log entry

### Day 26 — Router v1 (rules baseline)
- [ ] Implement rules baseline: keyword/regex + embedding-similarity to intent examples
- [ ] Create `routing_log` table (§9.1) and start logging every routing decision **from day one**, even at rules-baseline quality
- [ ] Build log entry

### Day 27 — Router distillation data
- [ ] Generate 10–30k labeled routing decisions using **T3 + reasoning on** as teacher
- [ ] Filter by teacher self-consistency (drop low-agreement labels)
- [ ] Build log entry

### Day 28 — Router SLM
- [ ] LoRA fine-tune Qwen3-1.7B on the distilled routing data
- [ ] Serve it as a LoRA adapter on the T1/T2 base (multi-LoRA — no extra GPU cost)
- [ ] Swap the rules baseline for the SLM in the live path
- [ ] Build log entry

### Day 29 — Structured output + escalation
- [ ] Enforce strict JSON output (vLLM structured output / xgrammar) for `{intent, tool, tool_args, model_tier, reasoning, confidence}`
- [ ] Implement escalation policy: `confidence < 0.6` → bump one tier, re-ask model to self-check
- [ ] Measure routing accuracy against a small hand-labeled set as a sanity number (not the full Phase 5 benchmark)
- [ ] Build log entry

### Day 30 — Model Manager — core
- [ ] Implement `EvictionPolicy` protocol + `ModelEntry` dataclass (tier, vram_gb, loaded_at, last_used, in_flight, load_time_s, pinned)
- [ ] Implement `LRUPolicy` (baseline): evict least-recently-used non-pinned model
- [ ] Phase 3 scope: manager controls vLLM **processes** on the box (pinned `CUDA_VISIBLE_DEVICES` or second GPU slot) — not K8s yet
- [ ] Build log entry

### Day 31 — Model Manager — integration
- [ ] Pin T0 + T2 resident; T3 loads on-demand via the manager
- [ ] Wire cold-start metrics: every load/evict logged with cause (so eviction-policy experiments in Phase 5 have clean data)
- [ ] Manually trigger a load, an eviction, and confirm `in_flight > 0` blocks eviction
- [ ] Build log entry

### Day 32 — Redis Streams wiring
- [ ] Implement job envelope (`request_id`, `idempotency_key`, `payload`, `attempt`, `trace_id`)
- [ ] Wire `XADD`/consumer group (`inference-workers`) delivery to the worker
- [ ] Implement retry with backoff (1s / 4s / 16s), `attempt+1` on failure
- [ ] Build log entry

### Day 33 — Reliability hardening
- [ ] Implement DLQ (`dlq:inference` stream) + alert after 3 failed attempts
- [ ] Implement idempotent execution: `SET NX` on `idem:{key}` before side effects; duplicates short-circuit to stored result
- [ ] Implement `XAUTOCLAIM` reclaim for crashed-worker pending entries (idle > 30s)
- [ ] **Failure drill:** `kill -9` a worker mid-request → confirm the request still completes via retry/reclaim
- [ ] Build log entry

### Day 34 — Summarizer worker + Phase 3 close-out
- [ ] Implement summarizer: trigger every 5 new messages, `summarize(old_summary + last 5 exchanges)` using T0/T1
- [ ] Store versioned summaries in Postgres (`summaries.session_id, version, text, created_at`)
- [ ] Run a 20-turn synthetic conversation end-to-end; confirm prompt-token count stays **flat**, not growing
- [ ] Run the **full §4 lifecycle** once, start to finish (scrub → context → route → queue → tool → model → re-ID → persist → summarize) and record it as your Phase 3 demo trace
- [ ] Write Phase 3 exit report
- [ ] Exit criteria check: ✅ full §4 lifecycle runs end-to-end ✅ `kill -9` drill passes ✅ 20-turn conversation shows flat prompt-token growth
- [ ] Build log entry — explicitly write "Phase 3 done, Phase 4 (Kubernetes & Reliability) next"

**Do not start Phase 4 until Day 34's checklist is fully checked.**

---

## After Day 34
Phase 4 (Kubernetes & Reliability — manifests, KEDA, HPA, failure drills, SLO dashboards) is next. This is also where the real benchmarking discipline kicks in for Phase 5: golden workload + k6/Locust + LLM-judge quality scoring (1–5) + full TTFT/TPOT/throughput/VRAM matrix, each experiment ending in a written keep/kill decision. Phase 2/3 deliberately only checked *correctness* (tool-call validity, PII recall, routing accuracy) — say the word when you want the Phase 4/5 checklist built out the same way.
