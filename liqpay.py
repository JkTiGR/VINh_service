from fastapi import FastAPI, Request, HTTPException
import base64
import hashlib
import json
import sqlite3
import os
import logging
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not LIQPAY_PUBLIC_KEY or not LIQPAY_PRIVATE_KEY:
    raise ValueError("❌ Ошибка: LIQPAY_PUBLIC_KEY или LIQPAY_PRIVATE_KEY не заданы!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
DB_PATH = "crm.db"

async def update_order_status(order_id: int, status: str):
    """Обновляет статус заказа в базе данных."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
        conn.close()
        logger.info(f"✅ Заказ {order_id} обновлён до статуса '{status}'")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления заказа {order_id}: {e}")

async def send_telegram_notification(order_id: int, status: str):
    """Отправляет уведомление в Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠ Telegram Bot Token или Chat ID не заданы, уведомления не будут отправлены.")
        return
    
    message = f"📢 Оплата заказа #{order_id} подтверждена!\n🛒 Статус: {status}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info(f"✅ Уведомление о заказе #{order_id} отправлено в Telegram")
        else:
            logger.error(f"❌ Ошибка при отправке Telegram-уведомления: {response.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления: {e}")

@app.post("/api/payment_callback")
async def payment_callback(request: Request):
    """Обработчик уведомлений LiqPay о статусе платежа."""
    try:
        body = await request.body()
        data_encoded = request.headers.get("X-Liqpay-Data")
        signature = request.headers.get("X-Liqpay-Signature")

        if not data_encoded or not signature:
            raise HTTPException(status_code=400, detail="❌ Ошибка: Отсутствуют данные в заголовках")

        # Декодируем данные
        decoded_data = base64.b64decode(data_encoded).decode()
        payment_data = json.loads(decoded_data)

        # Проверяем подпись
        expected_signature = base64.b64encode(
            hashlib.sha1((LIQPAY_PRIVATE_KEY + data_encoded + LIQPAY_PRIVATE_KEY).encode()).digest()
        ).decode()

        if signature != expected_signature:
            logger.warning("⚠ Ошибка: Некорректная подпись платежа")
            return {"status": "error", "message": "Invalid signature"}

        # Получаем данные о заказе
        order_id = payment_data.get("order_id")
        status = payment_data.get("status")

        logger.info(f"📩 Получен статус платежа: {status} для заказа #{order_id}")

        # Если платеж успешен, обновляем статус заказа и отправляем уведомление
        if status in ["success", "sandbox", "wait_accept"]:
            await update_order_status(order_id, "paid")
            await send_telegram_notification(order_id, "Оплачено")
            return {"status": "success", "message": f"Заказ {order_id} оплачен!"}

        return {"status": "pending", "message": f"Статус платежа: {status}"}

    except Exception as e:
        logger.error(f"❌ Ошибка обработки платежа: {e}")
        return {"status": "error", "message": str(e)}
    
def get_liqpay_url(order_id: int, amount: float, currency="UAH"):
    """Генерирует ссылку на оплату через LiqPay."""
    data = {
        "public_key": LIQPAY_PUBLIC_KEY,
        "version": "3",
        "action": "pay",
        "amount": str(amount),
        "currency": currency,
        "description": f"Оплата заказа #{order_id}",
        "order_id": str(order_id),
        "sandbox": "1"  # 1 - тестовый режим, 0 - боевой
    }

    # Кодируем данные в Base64
    json_data = json.dumps(data)
    encoded_data = base64.b64encode(json_data.encode()).decode()

    # Генерируем подпись
    sign_str = LIQPAY_PRIVATE_KEY + encoded_data + LIQPAY_PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(sign_str.encode()).digest()).decode()

    payment_url = f"https://www.liqpay.ua/api/3/checkout?data={encoded_data}&signature={signature}"
    return payment_url

