FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY server/requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "server/run.py"]
