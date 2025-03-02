-- Удаляем старые таблицы (если существуют)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS parts;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS stock_deliveries;

-- Таблица пользователей (администраторы и клиенты)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    is_admin BOOLEAN DEFAULT 0
);

-- Таблица клиентов
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    vin TEXT NOT NULL UNIQUE,
    car_model TEXT,
    year INTEGER,
    mileage INTEGER
);

-- Таблица автомобилей клиентов
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    vin TEXT UNIQUE NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    mileage INTEGER NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

-- Каталог автозапчастей
CREATE TABLE parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    description TEXT,
    image_url TEXT
);

-- Заказы клиентов
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
    total_price REAL NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('cash', 'card', 'bank_transfer')),
    delivery_address TEXT,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

-- Детали заказа (запчасти, входящие в заказ)
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (part_id) REFERENCES parts (id) ON DELETE CASCADE
);

-- Поставщики запчастей
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    address TEXT
);

-- История поставок запчастей
CREATE TABLE stock_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    delivery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE CASCADE,
    FOREIGN KEY (part_id) REFERENCES parts (id) ON DELETE CASCADE
);
