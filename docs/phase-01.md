What Day 10 produced

experiments/baseline-report.md — real numbers at all four concurrency levels, 0 failures throughout:

┌─────────────┬──────────┬──────────┬────────────────┬─────────────┬──────────┐
│ Concurrency │ p95 TTFT │ p95 TPOT │ p95 end-to-end │ Throughput  │ Tokens/s │
├─────────────┼──────────┼──────────┼────────────────┼─────────────┼──────────┤
│ 1           │ 39 ms    │ 9.5 ms   │ 2.38 s         │ 1.14 req/s  │ 105      │
├─────────────┼──────────┼──────────┼────────────────┼─────────────┼──────────┤
│ 4           │ 40 ms    │ 11.4 ms  │ 2.72 s         │ 4.03 req/s  │ 391      │
├─────────────┼──────────┼──────────┼────────────────┼─────────────┼──────────┤
│ 16          │ 67 ms    │ 125 ms   │ 4.23 s         │ 10.56 req/s │ 957      │
├─────────────┼──────────┼──────────┼────────────────┼─────────────┼──────────┤
│ 64          │ 97 ms    │ 48 ms    │ 5.01 s         │ 20.44 req/s │ 1963     │
└─────────────┴──────────┴──────────┴────────────────┴─────────────┴──────────┘

The reusable driver is experiments/baseline_runner.py — when you move to the L40S, python3 experiments/baseline_runner.py regenerates the whole report. The report and build-log both state loudly that this is RTX 5060 (8 GB), not L40S, and that the L40S re-run replaces these numbers.

How to read it: TTFT is tiny (39–97 ms) because it's a 3B model on short prompts — the real cost of load shows up as end-to-end p95 climbing (2.4s → 5.0s) as requests queue, while token throughput scales cleanly to ~2000 tok/s. (The TPOT column is noisy — a bucket-granularity artifact of the delta-quantile math; trust the trend, not the third digit.)

Phase 1 exit criteria ✅. Do not start Phase 2 until the L40S re-run is a deliberate decision.

---
How to watch metrics / logs / traces

You have three observability tools in compose, at very different readiness levels. Here's the honest state and how to use each.

