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
# Đổi sang argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Init DB
os.makedirs("/data", exist_ok=True)
with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS thoughts (id INTEGER PRIMARY KEY, content TEXT, book_title TEXT, mood TEXT, user_id INTEGER)')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS resonances (
            user_id INTEGER, 
            thought_id INTEGER, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, thought_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(thought_id) REFERENCES thoughts(id)
        )
    ''')
    
# Models
class UserAuth(BaseModel):
    username: str
    password: str

class ThoughtCreate(BaseModel):
    content: str
    book_title: str
    mood: str  

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
        conn.execute("INSERT INTO thoughts (content, book_title, mood, user_id) VALUES (?, ?, ?, ?)", 
                     (item.content, item.book_title, item.mood, uid))
        conn.commit()
    return {"msg": "Saved"}

@app.get("/thoughts/random")
def get_random_thoughts():
    sql = """
        SELECT t.id, t.content, t.book_title, t.mood, u.username 
        FROM thoughts t 
        JOIN users u ON t.user_id = u.id 
        GROUP BY t.book_title 
        ORDER BY RANDOM() LIMIT 8
    """
    with get_db() as conn:
        rows = conn.execute(sql).fetchall()
    return {"results": [dict(r) for r in rows]}

@app.get("/thoughts/mine")
def get_my_thoughts(token: str):
    username = get_current_user(token)
    
    with get_db() as conn:
        user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        uid = user['id']

        # 1. Bài do mình viết (Created)
        sql_created = """
            SELECT t.id, t.content, t.book_title, t.mood, u.username 
            FROM thoughts t 
            JOIN users u ON t.user_id = u.id 
            WHERE u.id = ? 
            ORDER BY t.id DESC
        """
        created = conn.execute(sql_created, (uid,)).fetchall()

        # 2. Bài mình đã lưu (Saved)
        sql_saved = """
            SELECT t.id, t.content, t.book_title, t.mood, u.username 
            FROM thoughts t 
            JOIN resonances r ON t.id = r.thought_id
            JOIN users u ON t.user_id = u.id 
            WHERE r.user_id = ? 
            ORDER BY r.timestamp DESC
        """
        saved = conn.execute(sql_saved, (uid,)).fetchall()

    return {
        "created": [dict(r) for r in created],
        "saved": [dict(r) for r in saved]
    }

@app.get("/thoughts/search")
def search(q: str = ""):
    sql = "SELECT t.content, t.book_title, t.mood, u.username FROM thoughts t JOIN users u ON t.user_id = u.id WHERE t.book_title LIKE ? OR t.content LIKE ? ORDER BY t.id DESC LIMIT 20"
    val = f"%{q}%"
    with get_db() as conn:
        rows = conn.execute(sql, (val, val)).fetchall()
    return {"results": [dict(r) for r in rows]}

@app.post("/thoughts/{thought_id}/resonate")
def toggle_resonance(thought_id: int, token: str):
    username = get_current_user(token)
    try:
        with get_db() as conn:
            # Lấy user_id
            user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            uid = user['id']
            
            # Kiểm tra xem đã lưu chưa
            exist = conn.execute("SELECT 1 FROM resonances WHERE user_id=? AND thought_id=?", (uid, thought_id)).fetchone()
            
            if exist:
                # Nếu có rồi thì xóa (Unsave)
                conn.execute("DELETE FROM resonances WHERE user_id=? AND thought_id=?", (uid, thought_id))
                msg = "Unsaved"
            else:
                # Chưa có thì thêm (Save)
                conn.execute("INSERT INTO resonances (user_id, thought_id) VALUES (?, ?)", (uid, thought_id))
                msg = "Saved"
            conn.commit()
        return {"status": msg}
    except Exception as e:
        raise HTTPException(400, "Error processing resonance")
    
# API Kiểm tra trạng thái Resonate của 1 bài viết
@app.get("/thoughts/{thought_id}/resonated")
def is_resonated(thought_id: int, token: str):
    try:
        user = get_current_user(token)
        with get_db() as conn:
            # Lấy ID người dùng hiện tại
            u_row = conn.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()
            if not u_row: return {"resonated": False}
            
            # Kiểm tra trong bảng resonances
            exist = conn.execute("SELECT 1 FROM resonances WHERE user_id=? AND thought_id=?", (u_row['id'], thought_id)).fetchone()
            return {"resonated": True if exist else False}
    except:
        return {"resonated": False}

# API Xóa bài viết (Chỉ chủ sở hữu mới được xóa)
@app.delete("/thoughts/{thought_id}")
def delete_thought(thought_id: int, token: str):
    user = get_current_user(token)
    with get_db() as conn:
        u_row = conn.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()
        if not u_row: raise HTTPException(401, "Invalid user")
        
        # Kiểm tra xem bài viết có phải của user này không
        t_row = conn.execute("SELECT user_id FROM thoughts WHERE id=?", (thought_id,)).fetchone()
        if not t_row: raise HTTPException(404, "Not found")
        if t_row['user_id'] != u_row['id']: raise HTTPException(403, "Not owner")

        # Xóa các Resonances liên quan trước (để sạch dữ liệu)
        conn.execute("DELETE FROM resonances WHERE thought_id=?", (thought_id,))
        # Xóa bài viết
        conn.execute("DELETE FROM thoughts WHERE id=?", (thought_id,))
        conn.commit()
    return {"msg": "Deleted"}