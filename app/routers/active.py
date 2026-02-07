from fastapi import APIRouter
from app.database import get_connection

router = APIRouter(
    prefix="/active-tables",
    tags=["Active Tables"]
)

@router.get("/")
def get_active_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Lấy danh sách bàn + trạng thái
            sql_tables = """
                SELECT 
                    tb.id            AS table_id,
                    tb.name          AS table_name,
                    tb.price_per_hour,
                    at.id            AS active_table_id,
                    at.is_active,
                    at.start_time,
                    at.player_name
                FROM table_billiard tb
                JOIN active_tables at 
                    ON tb.id = at.table_id
            """
            cursor.execute(sql_tables)
            tables = cursor.fetchall()

            # 2. Với mỗi bàn, lấy food + cue đang dùng
            for table in tables:
                active_id = table["active_table_id"]

                # foods
                cursor.execute("""
                    SELECT f.id, f.name, f.price, af.quantity
                    FROM active_table_foods af
                    JOIN foods f ON af.food_id = f.id
                    WHERE af.active_table_id = %s
                """, (active_id,))
                table["foods"] = cursor.fetchall()

                # cues
                cursor.execute("""
                    SELECT c.id, c.name, c.price, ac.rent_start_time
                    FROM active_table_cues ac
                    JOIN billiard_cues c ON ac.cue_id = c.id
                    WHERE ac.active_table_id = %s
                """, (active_id,))
                table["cues"] = cursor.fetchall()

            return tables
    finally:
        conn.close()
