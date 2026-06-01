FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn python-multipart

COPY app.py .

RUN mkdir -p demo_data

EXPOSE 8000

CMD ["python", "app.py"]
