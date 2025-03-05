import os
import logging
import requests

from flask import Flask, request, render_template, redirect, url_for, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# 1. Определяем базовую директорию и загружаем переменные окружения
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Если папка instance отсутствует, создаём её
instance_folder = os.path.join(basedir, 'instance')
if not os.path.exists(instance_folder):
    os.makedirs(instance_folder)

# 2. Создаём Flask‑приложение
app = Flask(__name__, static_folder="static")

# 3. Настройки приложения
# Формируем абсолютный путь к базе данных crm.db
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'crm.db')}"
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Настройка логирования
logging.basicConfig(level=logging.INFO)
app.logger.info("Запуск приложения")

# 5. Инициализация расширений
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "vin_bp.login"

# 6. Модель User
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), unique=True, nullable=False)  # Госномер
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# 7. Модель Client
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    vin = db.Column(db.String(50))
    car_model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)
    plate = db.Column(db.String(20))

# 8. Функция загрузки пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 9. Создаём Blueprint для маршрутов /vin.com
vin_bp = Blueprint('vin_bp', __name__, url_prefix='/vin.com')

# -------------------- Вспомогательная функция --------------------
def safe_int(val):
    try:
        return int(val.strip()) if val and val.strip() != '' else 0
    except Exception:
        return 0

# -------------------- Основные маршруты Blueprint --------------------
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
    # Если пользователь пытается открыть чужой дашборд, перенаправляем на свой
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
    """
    Создаёт новую запись в таблице Client (пример).
    """
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
    """
    Обновляет существующую запись (Client) по ID.
    """
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
    plate = request.args.get('plate', '').replace(" ", "").upper()
    client = Client.query.filter_by(plate=plate).order_by(Client.id.desc()).first()
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

# -------------------- Пример маршрута, который шлёт ссылку админу --------------------
@vin_bp.route('/send_admin', methods=['POST'])
@login_required
def send_admin():
    plate = current_user.plate
    link = f"http://127.0.0.1:5003/vin.com/dashboard/{plate}"
    admin_chat = os.getenv('ADMIN_CHAT_ID', "7371111768")
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    if not telegram_token:
        return jsonify({'status': 'error', 'message': 'TELEGRAM_TOKEN не задан'}), 500
    send_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": admin_chat, "text": f"Новый заказ: {link}"}
    r = requests.post(send_url, json=payload)
    if r.status_code == 200:
        return jsonify({'status': 'success', 'message': 'Ваши данные сохранены'})
    else:
        return jsonify({'status': 'error', 'message': r.text}), 500

# -------------------- Маршруты, отображающие шаблоны --------------------
@vin_bp.route('/home')
def home():
    return render_template('home.html')

@vin_bp.route('/diag')
def diag():
    return render_template('diag.html')

@vin_bp.route('/remont')
def remont():
    return render_template('remont.html')

@vin_bp.route('/parts')
def parts():
    return render_template('parts.html')

@vin_bp.route('/wash')
def wash():
    return render_template('wash.html')

@vin_bp.route('/shino')
def shino():
    return render_template('shino.html')

@vin_bp.route('/VK')
def VK():
    return render_template('VK.html')

@vin_bp.route('/visit')
def visit():
    return render_template('visit.html')

@vin_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    message = None
    if request.method == 'POST':
        plate = request.form.get('plate', '').replace(" ", "").upper()
        user = User.query.filter_by(plate=plate).first()
        if user:
            message = "Инструкции по восстановлению пароля отправлены"
        else:
            error = "Пользователь с данным госномером не найден"
    return render_template('forgot_password.html', error=error, message=message)

# -------------------- Главный маршрут /submit_order (пример сохранения + Telegram) --------------------
@app.route('/submit_order', methods=['POST'])
def submit_order():
    """
    Пример: Принимает JSON, сохраняет в Client и отправляет уведомление в Telegram.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Нет данных"}), 400

    # 1. Сохраняем данные в БД
    try:
        client_name = data.get('clientName', 'Не указано')
        phone = data.get('phone', 'Не указано')
        vin = data.get('vin', '').upper()
        car_model = data.get('carModel', 'Не указана')
        year = safe_int(data.get('year', '0'))
        mileage = safe_int(data.get('mileage', '0'))
        plate = data.get('plate', '').replace(" ", "").upper()

        new_client = Client(
            client_name=client_name,
            phone=phone,
            vin=vin,
            car_model=car_model,
            year=year,
            mileage=mileage,
            plate=plate
        )
        db.session.add(new_client)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Ошибка при сохранении: {e}")
        db.session.rollback()
        return jsonify({"error": f"Ошибка сохранения: {str(e)}"}), 500

    # 2. Отправляем сообщение в Telegram
    telegram_token = os.getenv("TELEGRAM_TOKEN", "")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID", "")
    if telegram_token and admin_chat_id:
        message = (
            f"Новый заказ #{new_client.id}:\n"
            f"Имя клиента: {client_name}\n"
            f"Телефон: {phone}\n"
            f"VIN: {vin}\n"
            f"Авто: {car_model} ({year})\n"
            f"Пробег: {mileage}\n"
            f"Номерной знак: {plate}\n"
        )
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                json={"chat_id": admin_chat_id, "text": message}
            )
            if resp.status_code != 200:
                app.logger.error(f"Ошибка Telegram: {resp.text}")
        except Exception as e:
            app.logger.error(f"Ошибка при запросе к Telegram: {e}")
    else:
        app.logger.warning("TELEGRAM_TOKEN или ADMIN_CHAT_ID не заданы, Telegram не отправлен.")

    # 3. Возвращаем JSON об успехе
    return jsonify({"message": "Данные успешно сохранены"}), 200

# -------------------- Обработчики ошибок --------------------
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

# 11. Точка входа
if __name__ == '__main__':
    with app.app_context():
        # Создаём таблицы в базе данных, если они ещё не существуют
        db.create_all()
    app.run(host="0.0.0.0", port=5003, debug=True)
