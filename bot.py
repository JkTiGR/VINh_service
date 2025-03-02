import logging
import os
import sqlite3
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import HTTPException
from api import app, DB_PATH
from liqpay import get_liqpay_url

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Ensure TELEGRAM_BOT_TOKEN is defined
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "http://127.0.0.1:8000"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден. Проверьте .env!")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Привет! Это бот VINh Service. Чем могу помочь?\n\n"
                                    "/create Имя Телефон [VIN] - Создать клиента\n"
                                    "/clients - Список клиентов\n"
                                    "/order Клиент_ID Запчасть_ID Кол-во - Создать заказ\n"
                                    "/orders - Список заказов\n"
                                    "/orderinfo ID - Информация о заказе")

# Создание клиента
async def create_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠ Использование: /create Имя Телефон [VIN]")
        return

    name = args[0]
    phone = args[1]
    vin = args[2] if len(args) > 2 else "Не указан"

    payload = {"name": name, "phone": phone, "vin": vin}
    try:
        response = requests.post(f"{API_URL}/clients/", json=payload)
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Клиент {name} успешно создан!")
        else:
            await update.message.reply_text(f"❌ Ошибка при создании клиента: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {e}")

# Получение списка клиентов
async def list_clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{API_URL}/clients/")
        if response.status_code == 200:
            clients = response.json()
            message = "📋 **Список клиентов:**\n"
            for client in clients:
                message += f"🔹 {client['id']}: {client['name']} - {client['phone']} (VIN: {client['vin']})\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Ошибка при получении списка клиентов.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {e}")

# Создание заказа
async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("⚠ Использование: /order Клиент_ID Запчасть_ID Кол-во")
        return

    client_id = args[0]
    part_id = args[1]
    quantity = int(args[2])

    payload = {
        "client_id": client_id,
        "payment_method": "cash",
        "delivery_address": "На месте",
        "items": [{"part_id": part_id, "quantity": quantity, "price": 0}]
    }

    try:
        response = requests.post(f"{API_URL}/orders/", json=payload)
        if response.status_code == 200:
            await update.message.reply_text(f"✅ Заказ для клиента {client_id} успешно создан!")
        else:
            await update.message.reply_text(f"❌ Ошибка при создании заказа: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {e}")

# Получение списка заказов
async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{API_URL}/orders/")
        if response.status_code == 200:
            orders = response.json()
            message = "📦 **Список заказов:**\n"
            for order in orders:
                message += f"🔹 {order['id']}: Клиент {order['client_id']}, статус: {order['status']}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Ошибка при получении списка заказов.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {e}")

# Получение информации о заказе
async def order_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("⚠ Использование: /orderinfo ID_заказа")
        return

    order_id = args[0]

    try:
        response = requests.get(f"{API_URL}/orders/{order_id}")
        if response.status_code == 200:
            order = response.json()
            message = f"📦 **Информация о заказе {order_id}:**\n"
            message += f"👤 Клиент: {order['client_id']}\n"
            message += f"🛒 Статус: {order['status']}\n"
            message += f"💰 Сумма: {order['total_price']} UAH\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"❌ Заказ {order_id} не найден.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {e}")

# Обработка неизвестных команд
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Извините, я не понимаю эту команду.")

async def pay_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерация ссылки на оплату через LiqPay."""
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("⚠ Использование: /pay ID_заказа")
        return

    order_id = args[0]

    try:
        response = requests.get(f"{API_URL}/payment/{order_id}")
        if response.status_code == 200:
            payment_data = response.json()
            await update.message.reply_text(f"💳 Оплата заказа #{order_id}:\n{payment_data['payment_url']}")
        else:
            await update.message.reply_text("❌ Ошибка при генерации платежной ссылки.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# Запуск бота
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_client))
    application.add_handler(CommandHandler("clients", list_clients))
    application.add_handler(CommandHandler("order", create_order))
    application.add_handler(CommandHandler("orders", list_orders))
    application.add_handler(CommandHandler("orderinfo", order_info))
    application.add_handler(CommandHandler("pay", pay_order))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()

if __name__ == "__main__":
    main()
