from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    Модель пользователя.
    Логин – госномер автомобиля.
    """
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), unique=True, nullable=False)  # Госномер
    password = db.Column(db.String(100), nullable=False)             # Хэш пароля
    is_admin = db.Column(db.Boolean, default=False)                  # Флаг администратора
    telegram_id = db.Column(db.String(50), unique=True, nullable=True) # Telegram ID (для интеграции с ботом)

class Client(db.Model):
    """
    Модель клиента.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    vin = db.Column(db.String(50), unique=True, nullable=False)
    car_model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    """
    Модель заказа.
    Заказ связан с клиентом через внешний ключ.
    """
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    work_list = db.Column(db.Text, nullable=False)  # Перечень работ
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
