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
  - 