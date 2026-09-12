from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Jerry Executive Agent API",
    description="Backend API powering the Jerry AI Executive Agent",
    version="0.1.0",
)

# CORS middleware configuration
origins = [
    "http://localhost:3000",
    "https://jerry-t5rd.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from starlette.middleware.sessions import SessionMiddleware

# Session middleware configuration for OAuth2 PKCE state
app.add_middleware(SessionMiddleware, secret_key="jerry-secure-session-key")

from app.api.auth import router as auth_router
from app.api.command import router as command_router

app.include_router(auth_router)
app.include_router(command_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
