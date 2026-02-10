from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import active   # hoặc đúng path router của bạn

app = FastAPI()

# ===============================
# ✅ CORS CONFIG (QUAN TRỌNG)
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# ROUTERS
# ===============================
app.include_router(active.router)

@app.get("/")
def root():
    return {"status": "OK"}
