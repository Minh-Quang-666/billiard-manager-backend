from fastapi import APIRouter
from app.database import get_connection

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("/")
def cleanup_history():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM play_history")
        conn.commit()

        return {
            "status": "success",
            "message": "play_history cleared"
        }

    finally:
        conn.close()
