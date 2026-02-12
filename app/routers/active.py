from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.database import get_connection
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/active-tables",
    tags=["Active Tables"],
    dependencies=[Depends(get_current_user)]
)

# =========================================================
# GET ACTIVE TABLES
# =========================================================
@router.get("/")
def get_active_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
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
            """)
            tables = cursor.fetchall()

            for table in tables:
                active_id = table["active_table_id"]

                cursor.execute("""
                    SELECT f.id, f.name, f.price, af.quantity
                    FROM active_table_foods af
                    JOIN foods f ON af.food_id = f.id
                    WHERE af.active_table_id = %s
                """, (active_id,))
                table["foods"] = cursor.fetchall()

                cursor.execute("""
                    SELECT c.id, c.name, c.price, ac.rent_start_time, ac.quantity
                    FROM active_table_cues ac
                    JOIN billiard_cues c ON ac.cue_id = c.id
                    WHERE ac.active_table_id = %s
                """, (active_id,))
                table["cues"] = cursor.fetchall()

            return tables
    finally:
        conn.close()


# =========================================================
# POST CHECKOUT (END TIME FROM FRONTEND)
# =========================================================
@router.post("/{table_id}/checkout")
def checkout_table(table_id: str, payload: dict):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            # 1. Validate payload
            if "end_time" not in payload:
                raise HTTPException(status_code=400, detail="end_time is required")

            end_time = datetime.strptime(payload["end_time"], "%Y-%m-%d %H:%M:%S")

            # 2. Lấy active table
            cursor.execute("""
                SELECT 
                    at.id,
                    at.start_time,
                    at.player_name,
                    tb.price_per_hour
                FROM active_tables at
                JOIN table_billiard tb ON tb.id = at.table_id
                WHERE at.table_id = %s AND at.is_active = 1
            """, (table_id,))
            active = cursor.fetchone()

            if not active:
                raise HTTPException(status_code=404, detail="Table is not active")

            active_id = active["id"]
            start_time = active["start_time"]
            player_name = active["player_name"]
            price_per_hour = float(active["price_per_hour"])  # ✅ FIX

            duration_seconds = int((end_time - start_time).total_seconds())

            # 3. Tiền bàn
            table_money = (duration_seconds / 3600) * price_per_hour

            # 4. Tiền đồ ăn
            cursor.execute("""
                SELECT SUM(f.price * af.quantity) AS food_money
                FROM active_table_foods af
                JOIN foods f ON af.food_id = f.id
                WHERE af.active_table_id = %s
            """, (active_id,))
            food_money = cursor.fetchone()["food_money"] or 0
            food_money = float(food_money)  # ✅ FIX

            # 5. Tiền gậy (GIÁ CỐ ĐỊNH)
            cursor.execute("""
                SELECT c.price, ac.quantity
                FROM active_table_cues ac
                JOIN billiard_cues c ON ac.cue_id = c.id
                WHERE ac.active_table_id = %s
            """, (active_id,))

            cue_money = sum(float(c["price"]) * c["quantity"] for c in cursor.fetchall())

            total_amount = int(table_money + food_money + cue_money)

            # 6. Lưu history
            cursor.execute("""
                INSERT INTO play_history (
                    table_id,
                    start_time,
                    end_time,
                    duration_seconds,
                    player_name,
                    total_amount
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                table_id,
                start_time,
                end_time,
                duration_seconds,
                player_name,
                total_amount
            ))

            # 7. Clear active data
            cursor.execute("DELETE FROM active_table_foods WHERE active_table_id = %s", (active_id,))
            cursor.execute("DELETE FROM active_table_cues WHERE active_table_id = %s", (active_id,))
            cursor.execute("""
                UPDATE active_tables
                SET is_active = 0, start_time = NULL, player_name = NULL
                WHERE id = %s
            """, (active_id,))

            conn.commit()

            return {
                "message": "Checkout success",
                "table_id": table_id,
                "duration_seconds": duration_seconds,
                "total_amount": total_amount
            }

    except Exception as e:
        conn.rollback()
        print("CHECKOUT ERROR:", e)  # 🔥 LOG RA CHO DỄ DEBUG
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


# =========================================================
# START TABLE  (NEW - 1.0.4)
# =========================================================
@router.post("/{table_id}/start")
def start_table(table_id: str, payload: dict):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            player_name = payload.get("player_name")
            if not player_name:
                raise HTTPException(status_code=400, detail="player_name is required")

            cursor.execute("""
                SELECT is_active FROM active_tables
                WHERE table_id = %s
            """, (table_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Table not found")

            if row["is_active"] == 1:
                raise HTTPException(status_code=400, detail="Table already active")

            cursor.execute("""
                UPDATE active_tables
                SET 
                    is_active = 1,
                    start_time = NOW(),
                    player_name = %s
                WHERE table_id = %s
            """, (player_name, table_id))

            conn.commit()

            return {
                "message": "Start table success",
                "table_id": table_id,
                "player_name": player_name
            }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# =========================================================
# LIST ALL FOODS
# =========================================================
@router.get("/foods")
def list_foods():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("SELECT * FROM foods")
            return cursor.fetchall()
    finally:
        conn.close()

# =========================================================
# LIST ALL CUES
# =========================================================
@router.get("/cues")
def list_cues():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("SELECT * FROM billiard_cues")
            return cursor.fetchall()
    finally:
        conn.close()

# =========================================================
# UPDATE FOOD QUANTITY
# =========================================================
@router.post("/{table_id}/foods")
def update_food(table_id: str, payload: dict):
    conn = get_connection()
    try:
        food_id = payload.get("food_id")
        quantity = payload.get("quantity")

        if food_id is None or quantity is None:
            raise HTTPException(400, "food_id and quantity required")

        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                SELECT id FROM active_tables
                WHERE table_id = %s AND is_active = 1
            """, (table_id,))
            active = cursor.fetchone()
            if not active:
                raise HTTPException(404, "Table not active")

            active_id = active["id"]

            cursor.execute("""
                SELECT id FROM active_table_foods
                WHERE active_table_id = %s AND food_id = %s
            """, (active_id, food_id))
            row = cursor.fetchone()

            if row:
                if quantity <= 0:
                    cursor.execute(
                        "DELETE FROM active_table_foods WHERE id = %s",
                        (row["id"],)
                    )
                else:
                    cursor.execute("""
                        UPDATE active_table_foods
                        SET quantity = %s
                        WHERE id = %s
                    """, (quantity, row["id"]))
            else:
                if quantity > 0:
                    cursor.execute("""
                        INSERT INTO active_table_foods
                        (active_table_id, food_id, quantity)
                        VALUES (%s, %s, %s)
                    """, (active_id, food_id, quantity))

        conn.commit()
        return {"message": "Food updated"}

    finally:
        conn.close()

# =========================================================
# UPDATE CUE QUANTITY
# =========================================================
@router.post("/{table_id}/cues")
def update_cue(table_id: str, payload: dict):
    conn = get_connection()
    try:
        cue_id = payload.get("cue_id")
        quantity = payload.get("quantity")

        if cue_id is None or quantity is None:
            raise HTTPException(400, "cue_id and quantity required")

        with conn.cursor() as cursor:
            cursor.execute("SET time_zone = '+07:00'")
            cursor.execute("""
                SELECT id FROM active_tables
                WHERE table_id = %s AND is_active = 1
            """, (table_id,))
            active = cursor.fetchone()
            if not active:
                raise HTTPException(404, "Table not active")

            active_id = active["id"]

            cursor.execute("""
                SELECT id FROM active_table_cues
                WHERE active_table_id = %s AND cue_id = %s
            """, (active_id, cue_id))
            row = cursor.fetchone()

            if row:
                if quantity <= 0:
                    cursor.execute(
                        "DELETE FROM active_table_cues WHERE id = %s",
                        (row["id"],)
                    )
                else:
                    cursor.execute("""
                        UPDATE active_table_cues
                        SET quantity = %s
                        WHERE id = %s
                    """, (quantity, row["id"]))
            else:
                if quantity > 0:
                    cursor.execute("""
                        INSERT INTO active_table_cues
                        (active_table_id, cue_id, quantity)
                        VALUES (%s, %s, %s)
                    """, (active_id, cue_id, quantity))

        conn.commit()
        return {"message": "Cue updated"}

    finally:
        conn.close()