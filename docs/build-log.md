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
    - Added another service called `adminer` to be UI for postgres, open `http://localhost:8080` then type credentials (server is `postgres`)
    - known gap to remember: seed_data.py is NOT idempotent — re-running
      migrate again would insert another 1000 units on top of the existing
      ones. Fine for now (single dev, single run), but flagging it so
      future-me (or a teammate) doesn't accidentally double-seed later.

    - next: Day 3 — CI skeleton + observability stubs (Prometheus/Grafana/
      OTel containers, no dashboards yet, just prove they boot).