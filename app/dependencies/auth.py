from fastapi import Header, HTTPException

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Chưa đăng nhập")

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token không hợp lệ")

    token = authorization.split(" ")[1]

    # Ở đây chỉ check tồn tại token (vì ta không lưu server side)
    if not token:
        raise HTTPException(401, "Token rỗng")

    return token
