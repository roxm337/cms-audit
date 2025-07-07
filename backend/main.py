from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(title="Laravel & WordPress Vulnerability Tracker")
app.include_router(api_router, prefix="/api")
