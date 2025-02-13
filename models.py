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
    
    # Внешний ключ для привязки к пользователю
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Связь с заказами
    orders = db.relationship('Order', backref='client', lazy=True)
    
    def __repr__(self):
        return f"<Client {self.name} ({self.car_model})>"

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
