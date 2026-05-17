from repository.userRepository import get_users, get_userById

def getAllUsers()-> dict:
    return get_users()

def getUserById(id:str)-> dict:
    return get_userById(id)