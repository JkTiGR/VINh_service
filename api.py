from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()

# База данных SQLite (замените на PostgreSQL, если нужно)
DB_PATH = "crm.db"

class Client(BaseModel):
    id: int
    name: str
    phone: str
    vin: str

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Создание клиента
@app.post("/clients/")
def create_client(client: Client):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clients (id, name, phone, vin) VALUES (?, ?, ?, ?)",
                   (client.id, client.name, client.phone, client.vin))
    conn.commit()
    conn.close()
    return {"message": f"Клиент {client.name} создан!"}

# Получение списка клиентов
@app.get("/clients/", response_model=List[Client])
def get_clients():
    conn = get_db_connection()
    clients = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()
    return [dict(client) for client in clients]

# Запуск сервера FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
