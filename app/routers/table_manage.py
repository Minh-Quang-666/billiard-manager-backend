from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/tables",
    tags=["Table Management"],
    dependencies=[Depends(get_current_user)]
)

# =============================
# LIST TABLES
# =============================
@router.get("/")
def list_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                SELECT id, name, price_per_hour
                FROM table_billiard
                ORDER BY id
            """)
            return cursor.fetchall()
    finally:
        conn.close()

# =============================
# ADD TABLE
# =============================
@router.post("/")
def add_table(payload: dict):
    table_id = payload.get("id")
    name = payload.get("name")
    price = payload.get("price_per_hour")

    if not table_id or not name:
        raise HTTPException(400, "id và tên không được trống")
    if not isinstance(price, int) or price <= 0:
        raise HTTPException(400, "giá phải lớn hơn 0")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            # check exist
            cursor.execute(
                "SELECT id FROM table_billiard WHERE id = %s",
                (table_id,)
            )
            if cursor.fetchone():
                raise HTTPException(400, "Đã tồn tại bàn có id tương tự")

            # insert table
            cursor.execute("""
                INSERT INTO table_billiard (id, name, price_per_hour)
                VALUES (%s, %s, %s)
            """, (table_id, name, price))

            # insert active_tables
            cursor.execute("""
                INSERT INTO active_tables (table_id, is_active)
                VALUES (%s, 0)
            """, (table_id,))

        conn.commit()
        return {"message": "Bàn tạo thành công"}
    finally:
        conn.close()

# =============================
# UPDATE TABLE
# =============================
@router.put("/{table_id}")
def update_table(table_id: str, payload: dict):
    name = payload.get("name")
    price = payload.get("price_per_hour")

    if not name:
        raise HTTPException(400, "tên không được để trống")
    if not isinstance(price, int) or price <= 0:
        raise HTTPException(400, "giá phải lớn hơn 0")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                UPDATE table_billiard
                SET name = %s, price_per_hour = %s
                WHERE id = %s
            """, (name, price, table_id))

        conn.commit()
        return {"message": "Bàn cập nhật thành công"}
    finally:
        conn.close()

# =============================
# DELETE TABLE (CHECK ACTIVE)
# =============================
@router.delete("/{table_id}")
def delete_table(table_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            # 🔍 check bàn có đang active không
            cursor.execute("""
                SELECT is_active
                FROM active_tables
                WHERE table_id = %s
            """, (table_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(404, "Bàn không tồn tại")

            if row["is_active"] == 1:
                raise HTTPException(
                    status_code=400,
                    detail="❌ Bàn đang hoạt động, không thể xóa"
                )

            # ❌ chỉ xóa khi KHÔNG active
            cursor.execute(
                "DELETE FROM active_tables WHERE table_id = %s",
                (table_id,)
            )
            cursor.execute(
                "DELETE FROM table_billiard WHERE id = %s",
                (table_id,)
            )

        conn.commit()
        return {"message": "Bàn xóa thành công"}
    finally:
        conn.close()

