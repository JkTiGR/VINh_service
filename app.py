import os
import logging
import requests
from datetime import datetime

from flask import Flask, request, render_template, redirect, url_for, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Импортируем модели: db, User, Client
from models import db, User, Client

# 1. Определяем базовую директорию и загружаем переменные окружения
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Если папка instance отсутствует, создаём её
instance_folder = os.path.join(basedir, 'instance')
os.makedirs(instance_folder, exist_ok=True)

# Полный путь к базе данных (absolute path)
db_path = os.path.join(instance_folder, 'crm.db')

# 2. Создаём Flask‑приложение
app = Flask(__name__, static_folder="static")

# 3. Настройки приложения
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Настройка логирования
logging.basicConfig(level=logging.INFO)
app.logger.info("Запуск приложения")

# 5. Инициализация расширений
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "vin_bp.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

###############################################
# МОДЕЛИ (дублируются, если в models.py есть),
# либо импортируем их из models.py (как выше).
###############################################

# 9. Создаём Blueprint для маршрутов /vin.com
vin_bp = Blueprint('vin_bp', __name__, url_prefix='/vin.com')

# -------------------- Вспомогательная функция --------------------
def safe_int(val):
    """
    Безопасное преобразование строки в int.
    Если невозможно преобразовать, вернет 0.
    """
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0

###############################################
# МАРШРУТЫ BLUEPRINT
###############################################
@vin_bp.route('/')
def index():
    return render_template('visit.html')

@vin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').replace(" ", "").upper()
        password = request.form.get('password')
        user = User.query.filter_by(plate=plate).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('vin_bp.dashboard', plate=user.plate))
        else:
            error = "Неверные данные"
    return render_template('login.html', error=error)

@vin_bp.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    error = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').replace(" ", "").upper()
        password = request.form.get('password')
        user = User.query.filter_by(plate=plate, is_admin=True).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('vin_bp.admin_dashboard'))
        else:
            error = "Неверные данные или пользователь не является администратором"
    return render_template('login_admin.html', error=error)

@vin_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').replace(" ", "").upper()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not plate:
            error = "Госномер обязателен"
        elif password != confirm_password:
            error = "Пароли не совпадают"
        elif User.query.filter_by(plate=plate).first():
            error = "Пользователь с таким госномером уже существует"
        if error:
            return render_template('register.html', error=error)
        hashed_password = generate_password_hash(password)
        new_user = User(plate=plate, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('vin_bp.dashboard', plate=new_user.plate))
    return render_template('register.html', error=error)

@vin_bp.route('/dashboard/<plate>')
@login_required
def dashboard(plate):
    # Если пользователь пытается открыть чужой дашборд, перенаправляем
    if current_user.plate != plate:
        return redirect(url_for('vin_bp.dashboard', plate=current_user.plate))
    return render_template('dashboard.html', plate=plate)

@vin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access Denied", 403
    dashboard_data = None
    plate = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').replace(" ", "").upper()
        dashboard_data = Client.query.filter_by(plate=plate).order_by(Client.id.desc()).first()
    return render_template('admin_dashboard.html', dashboard=dashboard_data, plate=plate)

# -------------------- API-методы для сохранения/обновления --------------------
@vin_bp.route('/submit', methods=['POST'])
@login_required
def submit_client():
    data = request.get_json() if request.is_json else request.form
    try:
        client_data = {
            'client_name': data.get('clientName'),
            'phone': data.get('phone'),
            'vin': data.get('vin', '').upper(),
            'car_model': data.get('carModel') or "Не указана",
            'year': safe_int(data.get('year', '0')),
            'mileage': safe_int(data.get('mileage', '0')),
            'plate': data.get('plate', '').replace(" ", "").upper()
        }
    except Exception as e:
        app.logger.error(f"Ошибка при обработке данных: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

    new_client = Client(**client_data)
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'status': 'success', 'order_id': new_client.id})

@vin_bp.route('/update/<int:client_id>', methods=['POST'])
@login_required
def update_client(client_id):
    data = request.get_json() if request.is_json else request.form
    client = Client.query.get_or_404(client_id)

    if 'clientName' in data:
        client.client_name = data['clientName']
    if 'phone' in data:
        client.phone = data['phone']
    if 'vin' in data:
        client.vin = data['vin'].replace(" ", "").upper()
    if 'carModel' in data:
        client.car_model = data['carModel'] or "Не указана"
    if 'year' in data:
        client.year = safe_int(data['year'])
    if 'mileage' in data:
        client.mileage = safe_int(data['mileage'])
    if 'plate' in data:
        client.plate = data['plate'].replace(" ", "").upper()

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Запись обновлена', 'order_id': client.id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Ошибка при обновлении записи: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@vin_bp.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    plate_query = request.args.get('plate', '').replace(" ", "").upper()
    client = Client.query.filter_by(plate=plate_query).order_by(Client.id.desc()).first()
    if client:
        return jsonify(
            client_id=client.id,
            client_name=client.client_name,
            phone=client.phone,
            vin=client.vin,
            car_model=client.car_model,
            year=client.year,
            mileage=client.mileage,
            plate=client.plate
        )
    else:
        return jsonify(error="Данные для данного госномера не найдены"), 404

# --------------------
# Пример отправки ссылки админу
# --------------------
@vin_bp.route('/send_admin', methods=['POST'])
@login_required
def send_admin():
    plate_var = current_user.plate
    link = f"http://127.0.0.1:5003/vin.com/dashboard/{plate_var}"
    admin_chat = os.getenv('ADMIN_CHAT_ID')
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token or not admin_chat:
        return jsonify({'status': 'error', 'message': 'TELEGRAM_TOKEN не задан'}), 500
    send_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": admin_chat, "text": f"Новый заказ: {link}"}
    r = requests.post(send_url, json=payload)
    if r.status_code == 200:
        return jsonify({'status': 'success', 'message': 'Ваши данные сохранены'})
    else:
        return jsonify({'status': 'error', 'message': r.text}), 500

# --------------------
# Пример маршрута сохранения + Telegram
# --------------------
@app.route('/submit_order', methods=['POST'])
@login_required
def submit_order():
    data = request.form

    parts_selected = ", ".join(request.form.getlist('part'))
    indicators_selected = ", ".join(request.form.getlist('indicators'))

    # Если модель Client содержит поля work_list, parts_selected, indicators, notes, и т.д.
    # В противном случае уберите или добавьте поля в модель Client
    client = Client(
        client_name=data.get('clientName'),
        phone=data.get('phone'),
        vin=data.get('vin', '').upper(),
        # make=data.get('make'),
        car_model=data.get('carModel'),
        year=safe_int(data.get('year')),
        mileage=safe_int(data.get('mileage')),
        plate=data.get('plate', '').replace(" ", "").upper(),
        # work_list=data.get('workList', ''),
        # parts_selected=parts_selected,
        # indicators=indicators_selected,
        # notes=data.get('notes', '')
    )

    try:
        db.session.add(client)
        db.session.commit()
        # Текст сообщения для Telegram
        telegram_message = (
            f"🔔 Новый заказ:\n"
            f"Имя клиента: {client.client_name}\n"
            f"Телефон: {client.phone}\n"
            f"VIN: {client.vin}\n"
            f"Авто: {client.car_model} ({client.year})\n"
            f"Пробег: {client.mileage}\n"
            f"Госномер: {client.plate}\n"
            # f"Работы: {client.work_list}\n"
            # f"Запчасти: {client.parts_selected}\n"
            # f"Индикаторы: {client.indicators}\n"
        )
        bot_token = os.getenv("BOT_TOKEN")
        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        if bot_token and admin_chat_id:
            try:
                resp = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": admin_chat_id, "text": telegram_message}
                )
                if resp.status_code != 200:
                    app.logger.error(f"Ошибка Telegram: {resp.text}")
            except Exception as ex:
                app.logger.error(f"Ошибка при запросе к Telegram: {ex}")
        else:
            app.logger.warning("BOT_TOKEN или ADMIN_CHAT_ID не заданы в .env")

    except Exception as e:
        app.logger.error(f"Ошибка при сохранении заказа: {e}")
        db.session.rollback()
        return jsonify({"error": "Ошибка при сохранении заказа."}), 500

    return jsonify({"message": "Заказ сохранён и (при наличии токена) отправлен в Telegram!"}), 200

# --------------------
# Обработчики ошибок
# --------------------
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/vin.com/api') or request.is_json:
        return jsonify(error="Resource not found"), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/vin.com/api') or request.is_json:
        return jsonify(error="Internal server error"), 500
    return render_template('500.html'), 500

# 10. Регистрируем Blueprint
app.register_blueprint(vin_bp)

# Создаём таблицы (если нет)
with app.app_context():
    db.create_all()

# 11. Точка входа
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=True)

