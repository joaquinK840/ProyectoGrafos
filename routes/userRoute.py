from fastapi import APIRouter,HTTPException
from service.userService import getAllUsers,getUserById

router = APIRouter()

@router.get("")
def get_users():
    return getAllUsers()

@router.get("/user/{id}")
def get_user(id):
    try:
        return getUserById(id)
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))
    
