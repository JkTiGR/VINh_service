import os
import requests
import logging
from flask import Flask, request, render_template, redirect, jsonify, Blueprint, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Загрузка переменных окружения
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Если папка instance не существует, создаём её
instance_folder = os.path.join(basedir, 'instance')
if not os.path.exists(instance_folder):
    os.makedirs(instance_folder)

# Инициализация Flask-приложения
app = Flask(__name__, static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'crm.db')}"
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
app.logger.info("Запуск приложения")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "vin_bp.login"

# Проверка перед логированием current_user
with app.app_context():
    if current_user and hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
        app.logger.info(f"current_user: {current_user.__dict__}")
    else:
        app.logger.warning("⚠ current_user is None или не аутентифицирован.")

# Модели
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    vin = db.Column(db.String(50))
    car_model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)
    plate = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    app.logger.info(f"🔍 Loading user: {user}")
    return user

# Создаём Blueprint для приложения
vin_bp = Blueprint('vin_bp', __name__, url_prefix='/vin.com')

# Главная страница
@vin_bp.route('/')
def index():
    return render_template('visit.html')

# Вход пользователя
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

# Вход администратора
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

# Регистрация
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

# Личный кабинет
@vin_bp.route('/dashboard/<plate>')
@login_required
def dashboard(plate):
    app.logger.info(f"Запрос на dashboard: Текущий пользователь: {current_user.plate}, Запрошенный plate: {plate}")
    if current_user.plate != plate:
        app.logger.warning(f"Несоответствие plate! Ожидалось {current_user.plate}, но получено {plate}")
        return redirect(url_for('vin_bp.dashboard', plate=current_user.plate))
    return render_template('dashboard.html', plate=plate)

# Административная панель
@vin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access Denied", 403
    return render_template('admin_dashboard.html')

# API для загрузки данных
@vin_bp.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    plate = request.args.get('plate', '').replace(" ", "").upper()
    client = Client.query.filter_by(plate=plate).first()
    if client:
        return jsonify(client_name=client.client_name, phone=client.phone, vin=client.vin, car_model=client.car_model, year=client.year, mileage=client.mileage, plate=client.plate)
    else:
        return jsonify(error="Данные не найдены"), 404

# Обработка ошибок
@app.errorhandler(404)
def not_found_error(error):
    return jsonify(error="Resource not found"), 404 if request.is_json else render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify(error="Internal server error"), 500 if request.is_json else render_template('500.html'), 500

app.register_blueprint(vin_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5003, debug=True)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify(error="Resource not found"), 404 if request.is_json else render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify(error="Internal server error"), 500 if request.is_json else render_template('500.html'), 500

