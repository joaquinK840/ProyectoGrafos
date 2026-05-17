import json
import os
from config import USER_JSON_PATH

def get_users()-> dict:
    if not os.path.exists(USER_JSON_PATH):
        raise ValueError(f"the users file do not exist{USER_JSON_PATH}")
    with open (USER_JSON_PATH,"r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            raise ValueError (f"the data with users data is not a valid JSON")
    

def get_userById(id:str) -> dict :
    users = get_users()
    if id not in users:
        raise ValueError(f"the user with {id} do not exist")
    return users[id]
