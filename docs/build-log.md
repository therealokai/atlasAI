- Day 0:

    - did `nvidia-smi` on my laptop, with arguments `nvidia-smi --query-gpu=name,compute_cap,memory.free,memory.used,memory.total --format=csv` and got output: 
        ```text
        name, compute_cap, memory.free [MiB], memory.used [MiB], memory.total [MiB]
        NVIDIA GeForce RTX 5060 Laptop GPU, 12.0, 7633 MiB, 76 MiB, 8151 MiB
        ```

    - checked my `docker --version` and got `Docker version 29.6.1, build 8900f1d`

    - Built the `build-log.md` file


    
- Day 1:
    - built project monoskeleton for the project with command:
        ```bash
        mkdir -p services/gateway services/router services/worker \
         mcp deploy experiments eval docs
         ```
    - created .env file, a copy from .env.example
    - built `docker-compose.yml` file with 3 services (postgres,qdrant,redis) and tested it with commands:
        ```bash
        # Postgres
        docker exec -it realestate-postgres psql -U realestate -d realestate -c "\dt"

        # Qdrant — open in browser
        open http://localhost:6333/dashboard   # (or just curl http://localhost:6333/collections)

        # Redis
        docker exec -it realestate-redis redis-cli ping   # should return PONG
        ```
- Day 2:
    - 

    - Added new service called `migrate` that have `profiles:["tools"]` which means it won't be launched/executed with `docker compose up` I've to run :
        ```bash
                docker compose --profile tools run --rm migrate
        ```
    - here, `--profile tools` means it activate the tools profile for this so it turns it on. `run` means run it and `-- rm migrate` means remove the container after finishing, Without this, every time you ran migrate you'd accumulate stopped containers named realestate-migrate, realestate-migrate-run-2, etc. cluttering docker ps -a.

    - verified:
        ```bash
                docker exec -it realestate-postgres psql -U realestate -d realestate -c "SELECT count(*) FROM units;"
                # → 1000 rows, correct
        ```
    - Added another service called `adminer` to be UI for postgres, open 
      ```bash
          http://localhost:8080    
      ```    
      then type credentials (server is `postgres`)
    - known gap to remember: seed_data.py is NOT idempotent — re-running
      migrate again would insert another 1000 units on top of the existing
      ones. Fine for now (single dev, single run), but flagging it so
      future-me (or a teammate) doesn't accidentally double-seed later.

    - next: Day 3 — CI skeleton + observability stubs (Prometheus/Grafana/
      OTel containers, no dashboards yet, just prove they boot).
- Day 3:
    - added CI skeleton: .github/workflows/ci.yml with 3 parallel jobs
      (lint via ruff, test via pytest, docker-build for the gateway
      Dockerfile). Kept dev tools (ruff, pytest) in a separate
      requirements-dev.txt so they never end up in a production image.
    - added a placeholder gateway Dockerfile (installs deps, no real app
      yet — real app arrives Day 7) so CI's docker-build job has
      something genuine to verify.
    - wrote a real (if tiny) placeholder test that imports Day 2's models
      and checks table names/columns, instead of a meaningless assert True.
    - pushed a trivial commit, confirmed all 3 CI jobs green in the
      Actions tab.
    - added prometheus + grafana + otel-collector to docker-compose.yml.
      prometheus scrapes only itself for now (no real app metrics exist
      yet); grafana has no datasource wired in yet (manual one-time setup);
      otel-collector uses a "debug" exporter since nothing sends it real
      telemetry yet. All three verified booting cleanly, no crash-loops.
    - To check prometheus:
      ```bash
          http://localhost:9090/query
      ```
      go to Status → Targets, confirm the prometheus job shows UP.
    - To check Grafana:
      ```bash
          http://localhost:3000/
      ```
      if it is open that's okay it means grafana works 
      log in with admin / admin (I've changed the password don't forget it)
    - To check OTel collector: 
      Type:
      ```bash
        docker compose logs otel-collector
      ``` 
      you want to see it report the pipeline started, with no repeated crash/restart lines.

    - next: Day 4 — add healthcheck blocks across all services and
      confirm `docker compose ps` shows everything (healthy), not just
      running.

- Day 4:
  - Actually, we did nothing as almost all health checks were done in day 3 

- Day 5:
  - Created a small document about phase0
- Day 6:
  - Tried `Qwen/Qwen2.5-3B-Instruct-AWQ` and it worked well on my laptop and I had to run `export VLLM_USE_FLASHINFER_SAMPLER=0` first.
- Day 7:
  - added `vllm/vllm-openai:latest` as a service with docker compose file
  - Created simple `fastapi` app with `health` and `chat` to test vLLM.
  - wired vllm + gateway into compose, gateway/health passes through to vllm/health,
  - to test vllm: `curl http://localhost:8081/health`
  - the actual pass:
    ```bash
    curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "Qwen/Qwen2.5-3B-Instruct-AWQ",
      "messages": [
        {
          "role": "user",
          "content": "مرحبا، عرفني بنفسك باختصار"
        }
      ]
    }'
    ```
  - next question: does gateway need a request timeout retry before Day 8's golden-set run hits it at volume?
- Day 8:
  - Created `run_golden_set.py` script to run on the `golden-set-v1.json` with vLLM with model `Qwen/Qwen2.5-3B-Instruct-AWQ` and save the response and the model name

- Day 9:
  - did: wrote `eval/k6-golden-set.js` — replays all 200 golden prompts
    against the gateway `/v1/chat` pass-through at a configurable
    concurrency (`-e CONCURRENCY=`). Ran it with no host install via the
    official image + host network:
    ```bash
    docker run --rm -i --network host -v "$PWD/eval:/eval" \
      grafana/k6 run -e CONCURRENCY=1 /eval/k6-golden-set.js
    ```
  - did: wired Prometheus to scrape vLLM. Added a `vllm` scrape job in
    `deploy/prometheus/prometheus.yml` (target `vllm:8000`, compose
    service name), `docker compose restart prometheus`, confirmed both
    targets show UP at `http://localhost:9090/` → Status → Targets. This
    is where Day 10's p95 TTFT/TPOT come from — vLLM ships those
    histograms on `/metrics` out of the box.
  - did: plumbing check passed — k6 at concurrency 1 ran 200/200 iters,
    0 failures, 100% checks (status 200 + non-empty completion). End-to-end
    p95 = 2.37s, med 0.72s (concurrency 1; NOT the baseline — that's Day 10).
  - broke: nothing. k6 isn't installed on the host; ran it via docker
    instead of adding another local dependency.
  - next question: at concurrency 16/64 (Day 10), does the single
    RTX 5060 (8 GB) become the bottleneck before we can even read a clean
    p95 TTFT off vLLM's metrics?

- Day 10:
  - HARDWARE NOTE: everything so far, including this baseline, runs on my
    laptop's **RTX 5060 (8 GB)**, NOT the L40S (48 GB) the design doc's
    §1.3 SLOs assume. I'll move to the L40S later and re-run this exact
    sweep — the report is written so those numbers are the ones that
    replace these. Until then treat these as a laptop floor, not the
    baseline we quote to anyone.
  - did: wrote `experiments/baseline_runner.py` — drives the Day 9 k6
    script at concurrency 1/4/16/64 and writes `experiments/baseline-report.md`.
    p95 TTFT/TPOT + token throughput come from vLLM's `/metrics`
    histograms (snapshot before/after each run, quantile over the delta);
    end-to-end p95 + req throughput come from k6 (client side). Run with:
    ```bash
    python3 experiments/baseline_runner.py
    ```
  - did: full sweep, 0 failures at every level. Numbers (RTX 5060, 3B AWQ):
    | conc | p95 TTFT | p95 TPOT | p95 e2e | req/s | tok/s |
    |------|----------|----------|---------|-------|-------|
    | 1    | 39 ms    | 9.5 ms   | 2.38 s  | 1.14  | 105   |
    | 4    | 40 ms    | 11.4 ms  | 2.72 s  | 4.03  | 391   |
    | 16   | 67 ms    | 125 ms   | 4.23 s  | 10.56 | 957   |
    | 64   | 97 ms    | 48 ms    | 5.01 s  | 20.44 | 1963  |
  - read: even on 8 GB, p95 TTFT stays 39–97 ms (tiny model + short golden
    prompts) — miles under the 1.5 s SLO. Throughput scales cleanly to
    ~2000 tok/s at concurrency 64; the cost shows up as end-to-end p95
    climbing (2.4 s → 5.0 s) as requests queue. TPOT column is noisy
    (bucket-granularity artifact of the delta quantile) — read the trend,
    not the third digit.
  - Phase 1 EXIT CRITERIA: ✅ baseline report exists with real numbers at
    all four concurrency levels (`experiments/baseline-report.md`).
  - next: Phase 2 (Data & Tools) — Postgres/Qdrant ingest, MCP
    property-search + doc-qa, single-model agent loop. Do NOT start until
    the L40S re-run is a conscious decision, not an accident.