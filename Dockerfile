FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY . .

# Install project dependencies (from pyproject.toml)
RUN uv pip install --system --no-cache .

ENTRYPOINT ["python", "-m", "src.main"]
