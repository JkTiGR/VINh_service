import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден. Проверьте .env!")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Это бот VINh Service. Чем могу помочь?")

async def create_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /create Имя Телефон [VIN]")
        return
    name = args[0]
    phone = args[1]
    vin = args[2] if len(args) > 2 else "Не указан"
    api_url = "http://127.0.0.1:5001/vin.com/submit"
    payload = {"clientName": name, "phone": phone, "vin": vin, "carModel": "Не указана", "year": 0, "mileage": 0}
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            await update.message.reply_text(f"Клиент {name} успешно создан!")
        else:
            await update.message.reply_text(f"Ошибка при создании клиента: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Извините, я не понимаю эту команду.")

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_client))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.run_polling()

if __name__ == "__main__":
    main()
