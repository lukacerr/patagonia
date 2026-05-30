from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings

app = FastAPI(title="IT Patagonia GenAI task", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"]
    if settings.ENV == "development"
    else settings.CORS_ALLOW_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
