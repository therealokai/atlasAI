# Phase 1 Baseline Report

**Generated:** 2026-07-26 13:20 UTC  
**Hardware:** RTX 5060 Laptop GPU (8 GB) — *NOT* the L40S (48 GB) the design doc's SLOs assume. Numbers here are a laptop floor; re-run on the L40S for the real baseline.  
**Model:** Qwen/Qwen2.5-3B-Instruct-AWQ (`awq_marlin`, `--max-model-len 4096`, `--gpu-memory-utilization 0.55`)  
**Workload:** eval/golden-set-v1.json (200 prompts) replayed via eval/k6-golden-set.js  
**Latency sources:** TTFT/TPOT/token-throughput = vLLM `/metrics` (server-side); end-to-end p95 + req throughput = k6 (client-side).

| Concurrency | p95 TTFT | p95 TPOT | p95 end-to-end | Throughput | Tokens/s | Failed |
|---|---|---|---|---|---|---|
| 1 | 39 ms | 9.5 ms | 2380 ms | 1.14 req/s | 105 | 0.00% |
| 4 | 40 ms | 11.4 ms | 2720 ms | 4.03 req/s | 391 | 0.00% |
| 16 | 67 ms | 125.0 ms | 4230 ms | 10.56 req/s | 957 | 0.00% |
| 64 | 97 ms | 48.2 ms | 5010 ms | 20.44 req/s | 1963 | 0.00% |

## Against §1.3 SLO targets

| SLO | Target | Where we stand (this hardware) |
|---|---|---|
| p95 TTFT — tiny/strong tier | < 1.5 s | ✅ 39–97 ms across all levels (tiny 3B model + short prompts) |
| p95 end-to-end (tool call included) | < 8 s | no tools wired yet (Phase 2) — pure generation |
| Request success rate | ≥ 99.5% | 100% (0 failures) across all levels |

> These targets were written for the L40S. On an 8 GB laptop card the point is not to *hit* them but to have a durable, honest number to quote and to re-measure against once the L40S is in place.
