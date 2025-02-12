import os
import logging
import requests
from flask import Flask, request, render_template, redirect, jsonify, Blueprint, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask_migrate import Migrate
import models

# Определяем базовую директорию проекта
basedir = os.path.abspath(os.path.dirname(__file__))

# Загружаем переменные окружения из файла .env
env_path = os.path.join(basedir, ".env")
load_dotenv(env_path)

# Если папка instance не существует, создаём её
instance_folder = os.path.join(basedir, 'instance')
if not os.path.exists(instance_folder):
    os.makedirs(instance_folder)

# Создаем Flask-приложение
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'crm.db')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")

# Инициализируем базу данных и миграции
models.db.init_app(app)
migrate = Migrate(app, models.db)

# Настраиваем Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "vin_bp.login"

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# Добавляем маршрут для корневого URL, который перенаправляет на /vin.com/
@app.route("/")
def index_redirect():
    return redirect(url_for('vin_bp.index'))

# Регистрируем Blueprint для веб-интерфейса с префиксом /vin.com
vin_bp = Blueprint('vin_bp', __name__, url_prefix='/vin.com')

@vin_bp.route('/')
def index():
    return render_template('login.html')

@vin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        plate = request.form.get('plate', '').upper()
        password = request.form.get('password')
        user = models.User.query.filter_by(plate=plate).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('vin_bp.dashboard', plate=plate))
        return render_template('login.html', error='Неверные данные')
    return render_template('login.html')

@vin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('vin_bp.login'))

@vin_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        plate = request.form.get('plate', '').upper()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not plate:
            return render_template('register.html', error="Госномер обязателен")
        if password != confirm_password:
            return render_template('register.html', error="Пароли не совпадают")
        if models.User.query.filter_by(plate=plate).first():
            return render_template('register.html', error="Пользователь с таким госномером уже существует")
        hashed_password = generate_password_hash(password)
        new_user = models.User(plate=plate, password=hashed_password)
        models.db.session.add(new_user)
        models.db.session.commit()
        login_user(new_user)
        return redirect(url_for('vin_bp.dashboard', plate=plate))
    return render_template('register.html')

@vin_bp.route('/dashboard/<plate>')
@login_required
def dashboard(plate):
    if current_user.plate != plate:
        return redirect(url_for('vin_bp.dashboard', plate=current_user.plate))
    return render_template('dashboard.html', plate=plate)

@vin_bp.route('/submit', methods=['POST'])
@login_required
def submit_order():
    data = request.get_json() if request.is_json else request.form
    client_data = {
        'name': data.get('clientName'),
        'phone': data.get('phone'),
        'vin': data.get('vin'),
        'car_model': data.get('carModel', 'Не указана'),
        'year': int(data.get('year', 0)),
        'mileage': int(data.get('mileage', 0))
    }
    new_client = models.Client(**client_data)
    models.db.session.add(new_client)
    models.db.session.commit()
    return jsonify({'status': 'success', 'order_id': new_client.id})

@vin_bp.route('/send_admin', methods=['POST'])
@login_required
def send_admin():
    plate = current_user.plate
    link = f"http://127.0.0.1:5001/vin.com/dashboard/{plate}"
    admin_chat = "7371111768"
    send_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
    payload = {"chat_id": admin_chat, "text": f"Новый заказ: {link}"}
    r = requests.post(send_url, json=payload)
    if r.status_code == 200:
        return jsonify({'status': 'success', 'message': 'Ваши данные сохранены'})
    else:
        return jsonify({'status': 'error', 'message': r.text}), 500

# Регистрируем Blueprint
app.register_blueprint(vin_bp)

# --- Telegram-бот: отключён для продакшена ---
"""
# Асинхронные обработчики для Telegram-бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в CRM VINh AUTOSERVICE!")

async def create_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /create Имя Телефон [VIN]")
        return
    name = args[0]
    phone = args[1]
    vin = args[2] if len(args) > 2 else "Не указан"
    api_url = "http://127.0.0.1:5001/vin.com/submit"
    payload = {
        "clientName": name,
        "phone": phone,
        "vin": vin,
        "carModel": "Не указана",
        "year": 0,
        "mileage": 0
    }
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            await update.message.reply_text(f"Клиент {name} успешно создан!")
        else:
            await update.message.reply_text(f"Ошибка: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Извините, я не понимаю эту команду.")

if __name__ == "__main__":
    with app.app_context():
        models.db.create_all()
    # Запуск встроенного сервера Flask на порту 5001 с режимом отладки (для разработки)
    from threading import Thread
    def run_flask():
        app.run(host="0.0.0.0", port=5001, debug=True, threaded=True, use_reloader=False)
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    # Запуск Telegram-бота (для разработки)
    from telegram.ext import ApplicationBuilder, CommandHandler
    telegram_app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("create", create_client))
    telegram_app.add_handler(CommandHandler("unknown", unknown))
    telegram_app.run_polling()
"""

# Для продакшена: используется gunicorn, поэтому этот блок не выполняется.
if __name__ == "__main__":
    with app.app_context():
        models.db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)

