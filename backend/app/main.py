from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.com_router import router as com_router
from app.routers.doc_router import router as doc_router
from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.email_router import router as email_router
from app.routers.risk_router import router as risk_router


app = FastAPI(
    title="AI Trade Assistant Backend",
    description="Backend for trade communication, document generation, and risk analysis.",
    version="0.1.0",
)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(com_router, prefix="/api", tags=["communication"])
app.include_router(doc_router, prefix="/api", tags=["document"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(profile_router, prefix="/api", tags=["profile"])
app.include_router(email_router, prefix="/api", tags=["emails"])
app.include_router(risk_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend is running"}