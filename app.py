from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
import json
import logging
import os
import hashlib
import base64
import datetime
logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

@app.get('/')
async def start() -> str:
    return 'Helloworld'

@app.get('/register/{username}/{password}')
async def register(username:str,password:str):
    try:
        if len(username) <= 5 or len(password) <= 5 or " " in username or " " in password:
            print(1)
            raise HTTPException(status_code=400,detail='Пароль та юзернейм повинні бути більше 5 символів та не мати пробілів')                
        with open('players.json','r+') as file:
            bd = json.load(file)
            for user_name_dynamic in bd.keys():
                if user_name_dynamic.lower() == username.lower():
                    raise HTTPException(status_code=409,detail="Даний юзернейм вже використовується")
                    
    #роблю соль та хешую пароль
        salt = os.urandom(16) # 16 случайних бітів
        hash_password = hashlib.pbkdf2_hmac('sha256',password.encode(),salt=salt,iterations=10000) #10 тисяч раз хешую пароль
        salt = base64.b64encode(salt).decode()
        hash_password = base64.b64encode(hash_password).decode()
        now_time = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M')
        user_info = { 
                    
                    "password": {'salt':salt,'hash_password':hash_password},
                    'regist_date' : now_time
                    }




        bd.setdefault(username, user_info)
        with open('players.json','w') as file:
            json.dump(bd,file,indent=4)
        return {"status": "success", 'username':username,'regist_date':now_time}
    except FileNotFoundError as e:
        logging.error(f"Файл не найден.Запит не отриманий. Роблю json файл{e}")
        with open('players.json','w') as file:
            bd = {

                    'username': {
                    "password" :
                    {'salt': 'sdlsdkopwokd', 'hash_password': 'hash'},
                    'date_regist' :'regist_date'
                    }
                    }
            json.dump(bd, file,indent=4)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f'Щось пішло не так: \n ')
        
        print(e)
    
    return {"status": "Failed"}
    

@app.get('/login/{user}/{password}')
async def login(user:str,password:str):
    try:
        if len(user) <= 5 or len(password) <= 5 or " " in user or " " in password:
            
            raise HTTPException(status_code=400,detail='Пароль та юзернейм повинні бути більше 5 символів та не мати пробілів')                
        with open('players.json','r') as file:
            bd = json.load(file)
        if not(user in list(bd.keys())):
            raise HTTPException(status_code=409,detail="Даний юзернейм не використовується")
        salt = base64.b64decode(bd[user]['password']['salt'])
        hash_password =  base64.b64decode(bd[user]['password']['hash_password'])
        current_password = hashlib.pbkdf2_hmac('sha256',password.encode(),salt=salt,iterations=10000)
        if not(hash_password == current_password):
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
    with open('players.json','r') as file:
        return json.load(file)
