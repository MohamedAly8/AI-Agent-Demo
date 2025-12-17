FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend.py .
EXPOSE 8000
# Run uvicorn on 0.0.0.0 so it is accessible outside the container
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
