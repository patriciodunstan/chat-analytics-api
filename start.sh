#!/bin/sh
# Start script for Railway deployment
# Uses PORT environment variable if set, otherwise defaults to 8000

exec uvicorn app.main:app --host 0.0.0.0 --port 8000:8000
