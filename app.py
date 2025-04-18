from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,HTMLResponse
from pydantic import BaseModel,Field
import uvicorn
import os
import hashlib
import base64
import datetime
import logging
import re
import sqlite3
base = sqlite3.connect('bd/players.sqlite3')
connect = base.cursor()
#створюю таблицю якщо немає
connect.execute('''
CREATE TABLE IF NOT EXISTS players(
             id INTEGER PRIMARY KEY,
             name Text,
             hash_password Text,
             salt Text,
             date_regist TEXT,
             admin TEXT
             )
''')
base.commit()
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "uvicorn_logs.log",
            "formatter": "default",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)



class Pattern_Responce(BaseModel):
    name:str = Field(max_length=20,min_length=4, description="Ім'я має бути від 4 до 20 символів")
    password:str = Field(
        min_length=6,max_length=16,pattern = r'^[a-zA-Z0-9_\-\.@#$%^&*()+=\[\]{}|~]+$',
        description="Тільки англійські літери, цифри та стандартні символи без пробілу")


app = FastAPI()
@app.get('/',response_class=HTMLResponse)
async def start() -> str:
    with open('home.html', 'r', encoding="utf-8") as f:
        content = f.read()
    return  HTMLResponse(content)

@app.post('/register')
async def register(pattern:Pattern_Responce):
    try:
        username = pattern.name
        password = pattern.password
        pattern = r'^[a-zA-Z0-9_\-\.@]+$'
        
        connect.execute('SELECT 1 FROM players WHERE name = ?',(username,))
        result = connect.fetchone()
        print(result)
        if result:
            raise HTTPException(status_code=409, detail="Даний юзернейм вже використовується")
                    
    #роблю соль та хешую пароль
        salt = os.urandom(16) # 16 случайних бітів
        hash_password = hashlib.pbkdf2_hmac('sha256',password.encode(),salt=salt,iterations=10000) #10 тисяч раз хешую пароль
        salt = base64.b64encode(salt).decode()
        hash_password = base64.b64encode(hash_password).decode()
        now_time = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M')
        connect.execute('''
                        INSERT INTO players (name,hash_password,salt,date_regist) VALUES (?,?,?,?)
                        ''', (username,hash_password,salt,now_time))
        base.commit()
        return {"status": "success", 'username':username,'regist_date':now_time}
    except HTTPException as e:
        raise
    except Exception as e:
        
        print(e)
    return {"status": "Failed"}

@app.post('/login')
async def login(pattern:Pattern_Responce):
    try:
        username = pattern.name
        password = pattern.password
        pattern = r'^[a-zA-Z0-9_\-\.@]+$'
        connect.execute('SELECT 1 FROM players WHERE name = ?',(username,))
        result = connect.fetchone()
        print(result)
        if not(result):
            raise HTTPException(status_code=409, detail="Даний юзернейм не використовується")
        
        connect.execute('SELECT hash_password,salt FROM players WHERE name=?',(username,))
        hash_password, salt = connect.fetchone()
        hash_password = base64.b64decode(hash_password) 
        salt = base64.b64decode(salt)
        if  hash_password != hashlib.pbkdf2_hmac('sha256',password.encode(),salt=salt,iterations=10000):
            raise HTTPException(status_code=401,detail="Пароль не вірний")
        return {"status": "succes"}
    
        

    except HTTPException:
        raise
    
    except Exception as e:
        logging.error(f'Виникла помилка: {e}')
    return {"status": "Failed"}
#затичка
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("images.jpg")

@app.get('/alluser')
async def all():
    connect.execute("Select * From players")
    return connect.fetchone()

@app.get('/log/clear',response_class=HTMLResponse)
async def clear_log():
    try:
        os.remove('uvicorn_logs.log')
    except:
        pass
    with open("uvicorn_logs.log", "w") as file:
        file.write("")

    with open("clear_log.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content)

@app.get('/log', response_class=HTMLResponse)
async def log():
    with open('uvicorn_logs.log','r',encoding='utf-8') as file:
        content = file.readlines()
        html = f"""
<html>
    <head>
        <title>Логи сервера</title>
        <style>
            body {{
                font-family: monospace;
                background-color: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
            }}
            pre {{
                white-space: pre-wrap;
                word-break: break-word;
                background-color: #2d2d2d;
                padding: 20px;
                border-radius: 10px;
                overflow: auto;
                max-height: 90vh;
                font-size: 18px; /* Збільшений розмір тексту логів */
            }}
            .buttons-container {{
                display: flex;
                justify-content: center;
                gap: 20px; /* Відстань між кнопками */
                margin-bottom: 20px;
            }}
            button {{
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            button:hover {{
                background-color: #c0392b;
            }}
            .doc-btn {{
                background-color: #2980b9;
            }}
            .doc-btn:hover {{
                background-color: #1f6d8c;
            }}
        </style>
    </head>
    <body>
        <h1>Логи сервера</h1>
        <div class="buttons-container">
            <form action="/log/clear" method="get">
                <button type="submit">Очистити логи</button>
            </form>
            <form action="/" method="get">
                <button type="submit" class="doc-btn">Документація</button>
            </form>
        </div>
        <pre>
            {''.join([
                f'<span style="color: #2ecc71;">{line}</span><br>' if '200' in line else
                f'<span style="color: #e74c3c;">{line}</span><br>' if '500' in line else
                f'<span style="color: #f39c12;">{line}</span><br>'
                for line in reversed(content)
            ])}
        </pre>
    </body>
</html>
"""






        return html


        
    return 


@app.get('/freerobux', response_class=HTMLResponse)
async def profile():
    with open('fbi/no_virus.html','r',encoding='utf-8') as file:
        content = file.read()
    return HTMLResponse(content=content)






if __name__ == '__main__':
    try:
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
    except:
        connect.close()
        base.close()
        logging.debug('бд закрита')