from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import active   # hoặc đúng path router của bạn
from app.routers import table_manage
from app.routers import food_manage
from app.routers import cue_manage, auth

app = FastAPI()

# ===============================
# ✅ CORS CONFIG (QUAN TRỌNG)
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://billiard-manager-fe.vercel.app",
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
app.include_router(auth.router)
app.include_router(active.router)
app.include_router(table_manage.router)
app.include_router(food_manage.router)
app.include_router(cue_manage.router)

@app.get("/")
def root():
    return {"status": "OK"}
