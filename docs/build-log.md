- Day 0:

    - did `nvidia-smi` on my laptop, with arguments `nvidia-smi --query-gpu=name,compute_cap,memory.free,memory.used,memory.total --format=csv` and got output: 
        ```text
        name, compute_cap, memory.free [MiB], memory.used [MiB], memory.total [MiB]
        NVIDIA GeForce RTX 5060 Laptop GPU, 12.0, 7633 MiB, 76 MiB, 8151 MiB
        ```

    - checked my `docker --version` and got `Docker version 29.6.1, build 8900f1d`

    - Built the `build-log.md` file


    
