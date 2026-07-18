FROM python:3.11-slim

WORKDIR /app

# Real dependencies arrive properly on Day 7 when the actual gateway app
# is built. For now this just needs to install cleanly so CI's docker
# build step has something real to verify.
COPY requirements-day2.txt .
RUN pip install --no-cache-dir -r requirements-day2.txt

COPY . .

# Placeholder command — replaced with `uvicorn app:app ...` on Day 7.
CMD ["echo", "gateway placeholder - real app arrives Day 7"]
