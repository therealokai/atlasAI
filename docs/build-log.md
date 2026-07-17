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
