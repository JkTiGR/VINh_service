from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

# Инициализация базы данных
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    Модель пользователя.
    Логин – госномер автомобиля.
    """
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), unique=True, nullable=False)  # Госномер
    password = db.Column(db.String(100), nullable=False)  # Хэш пароля
    is_admin = db.Column(db.Boolean, default=False)  # Флаг администратора
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)  # Telegram ID (для интеграции с ботом)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с клиентами
    clients = db.relationship('Client', backref='user', lazy=True)
    
    def __repr__(self):
        return f"<User {self.plate}>"

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    vin = db.Column(db.String(50))
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)
    plate = db.Column(db.String(20))
    work_list = db.Column(db.Text)
    parts_selected = db.Column(db.Text)
    indicators = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Client {self.client_name} - {self.plate}>"


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
    
    def __repr__(self):
        return f"<Order {self.id} - {self.total_price} UAH>"
