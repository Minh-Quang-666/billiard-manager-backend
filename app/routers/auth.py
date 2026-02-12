from fastapi import APIRouter, HTTPException
from app.database import get_connection
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# token store tạm (đủ dùng cho app nhỏ)
TOKENS = {}

@router.post("/login")
def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(400, "Thiếu username hoặc password")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT password FROM users WHERE username = %s",
                (username,)
            )
            row = cursor.fetchone()

            if not row or row["password"] != password:
                raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")

        token = str(uuid.uuid4())
        TOKENS[token] = username

        return {
            "token": token,
            "username": username
        }
    finally:
        conn.close()


@router.post("/logout")
def logout(token: str):
    TOKENS.pop(token, None)
    return {"message": "Đã đăng xuất"}
