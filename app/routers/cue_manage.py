from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/cues",
    tags=["Cue Management"],
    dependencies=[Depends(get_current_user)]
)

# =============================
# LIST CUES
# =============================
@router.get("/")
def list_cues():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                SELECT id, name, price
                FROM billiard_cues
                ORDER BY id
            """)
            return cursor.fetchall()
    finally:
        conn.close()

# =============================
# ADD CUE
# =============================
@router.post("/")
def add_cue(payload: dict):
    cue_id = payload.get("id")
    name = payload.get("name")
    price = payload.get("price")

    if not cue_id or not name:
        raise HTTPException(400, "ID và tên không được trống")
    if not isinstance(price, int) or price <= 0:
        raise HTTPException(400, "Giá phải > 0")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute(
                "SELECT id FROM billiard_cues WHERE id = %s",
                (cue_id,)
            )
            if cursor.fetchone():
                raise HTTPException(400, "ID gậy đã tồn tại")

            cursor.execute("""
                INSERT INTO billiard_cues (id, name, price)
                VALUES (%s, %s, %s)
            """, (cue_id, name, price))

        conn.commit()
        return {"message": "Thêm gậy thành công"}
    finally:
        conn.close()

# =============================
# UPDATE CUE
# =============================
@router.put("/{cue_id}")
def update_cue(cue_id: str, payload: dict):
    name = payload.get("name")
    price = payload.get("price")

    if not name:
        raise HTTPException(400, "Tên không được trống")
    if not isinstance(price, int) or price <= 0:
        raise HTTPException(400, "Giá phải > 0")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                UPDATE billiard_cues
                SET name = %s, price = %s
                WHERE id = %s
            """, (name, price, cue_id))

        conn.commit()
        return {"message": "Cập nhật gậy thành công"}
    finally:
        conn.close()

# =============================
# DELETE CUE
# =============================
@router.delete("/{cue_id}")
def delete_cue(cue_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            # ❗ xóa luôn bên active_table_cues (KHÔNG CHECK)
            cursor.execute(
                "DELETE FROM active_table_cues WHERE cue_id = %s",
                (cue_id,)
            )
            cursor.execute(
                "DELETE FROM billiard_cues WHERE id = %s",
                (cue_id,)
            )

        conn.commit()
        return {"message": "Xóa gậy thành công"}
    finally:
        conn.close()
