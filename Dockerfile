FROM python:3.10-slim

# Install Poetry
RUN pip install --no-cache-dir poetry==1.5.1

WORKDIR /app

# Copy only poetry files first for caching
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

# Now copy the rest of the code
COPY . /app

# Expose the port for Flask (if needed)
EXPOSE 8080

CMD ["poetry", "run", "python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080", "--app", "app.main:app"]
