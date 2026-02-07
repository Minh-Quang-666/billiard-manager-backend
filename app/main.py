from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import active   # router active tables

app = FastAPI(
    title="Billiard Manager API",
    version="1.0.0"
)

# ✅ CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vue dev
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(active.router)

@app.get("/")
def root():
    return {"status": "ok"}
