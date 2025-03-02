from fastapi import FastAPI, HTTPException
import sqlite3
from liqpay import get_liqpay_url  # ✅ Теперь функция найдена!

DB_PATH = "crm.db"  # ✅ Указываем путь вручную



app = FastAPI()
DB_PATH = "crm.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/payment/{order_id}")
def generate_payment_link(order_id: int):
    """Генерация ссылки на оплату заказа через LiqPay."""
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Оплата невозможна (статус заказа не 'pending')")

    payment_url = get_liqpay_url(order_id, order["total_price"], "UAH")
    return {"order_id": order_id, "payment_url": payment_url}
