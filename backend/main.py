import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api import router
from database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


load_dotenv()

app = FastAPI(title="VoltStream API", version="1.0.0", lifespan=lifespan)

cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://192.168.0.114:5175",
    "https://voltstream-project-95144.web.app",
    "https://voltstream-project-95144.firebaseapp.com",
]
extra_origins = os.getenv("CORS_ORIGINS", "")
if extra_origins:
    cors_origins.extend(origin.strip() for origin in extra_origins.split(",") if origin.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
