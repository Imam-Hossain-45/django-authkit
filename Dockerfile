FROM python:3.12-slim

# Development image for the local example app.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

WORKDIR /app/example_django_app

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

EXPOSE 8000
