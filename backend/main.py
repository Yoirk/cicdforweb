from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import sqlite3, datetime, os

app = FastAPI()

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")
ALGO = "HS256"
DB_PATH = "/data/app.db"
# SỬA Ở ĐÂY: Đổi sang argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Init DB
os.makedirs("/data", exist_ok=True)
with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS thoughts (id INTEGER PRIMARY KEY, content TEXT, book_title TEXT, user_id INTEGER)')

# Models
class UserAuth(BaseModel):
    username: str
    password: str

class ThoughtCreate(BaseModel):
    content: str
    book_title: str

# Helpers
def create_token(data: dict):
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGO)

def get_current_user(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGO]).get("sub")
    except:
        raise HTTPException(401, "Invalid token")

# API
@app.post("/register")
def register(user: UserAuth):
    # Sẽ tự động dùng Argon2 để hash
    hashed = pwd_context.hash(user.password)
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user.username, hashed))
            conn.commit()
        return {"msg": "Created"}
    except:
        raise HTTPException(400, "Exists")

@app.post("/login")
def login(user: UserAuth):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (user.username,)).fetchone()
    # Verify cũng dùng Argon2
    if not row or not pwd_context.verify(user.password, row['password_hash']):
        raise HTTPException(401, "Bad credentials")
    return {"token": create_token({"sub": user.username})}

@app.post("/thoughts")
def add_thought(item: ThoughtCreate, token: str):
    user = get_current_user(token)
    with get_db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()['id']
        conn.execute("INSERT INTO thoughts (content, book_title, user_id) VALUES (?, ?, ?)", 
                     (item.content, item.book_title, uid))
        conn.commit()
    return {"msg": "Saved"}

@app.get("/thoughts/search")
def search(q: str = ""):
    sql = "SELECT t.content, t.book_title, u.username FROM thoughts t JOIN users u ON t.user_id = u.id WHERE t.book_title LIKE ? OR t.content LIKE ? ORDER BY t.id DESC LIMIT 20"
    val = f"%{q}%"
    with get_db() as conn:
        rows = conn.execute(sql, (val, val)).fetchall()
    return {"results": [dict(r) for r in rows]}