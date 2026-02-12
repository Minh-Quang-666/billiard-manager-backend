from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/foods",
    tags=["Food Management"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def list_foods():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                SELECT id, name, price
                FROM foods
                ORDER BY name
            """)
            return cursor.fetchall()
    finally:
        conn.close()

@router.post("/")
def add_food(payload: dict):
    food_id = payload.get("id")
    name = payload.get("name")
    price = payload.get("price")

    if not food_id or not name:
        raise HTTPException(400, "id và tên không được trống")
    if not isinstance(price, int) or price <= 0:
        raise HTTPException(400, "giá phải > 0")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute(
                "SELECT id FROM foods WHERE id = %s",
                (food_id,)
            )
            if cursor.fetchone():
                raise HTTPException(400, "Food đã tồn tại")

            cursor.execute("""
                INSERT INTO foods (id, name, price)
                VALUES (%s, %s, %s)
            """, (food_id, name, price))

        conn.commit()
        return {"message": "Thêm đồ ăn thành công"}
    finally:
        conn.close()


@router.put("/{food_id}")
def update_food(food_id: str, payload: dict):
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
                UPDATE foods
                SET name = %s, price = %s
                WHERE id = %s
            """, (name, price, food_id))

        conn.commit()
        return {"message": "Cập nhật đồ ăn thành công"}
    finally:
        conn.close()

@router.delete("/{food_id}")
def delete_food(food_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            # xóa ở active_table_foods trước
            cursor.execute(
                "DELETE FROM active_table_foods WHERE food_id = %s",
                (food_id,)
            )

            # xóa food
            cursor.execute(
                "DELETE FROM foods WHERE id = %s",
                (food_id,)
            )

        conn.commit()
        return {"message": "Xóa đồ ăn thành công"}
    finally:
        conn.close()
