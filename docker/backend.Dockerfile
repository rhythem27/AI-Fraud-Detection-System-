FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.5.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml .

# Install dependencies (no-interaction, no-ansi for cleaner logs)
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
