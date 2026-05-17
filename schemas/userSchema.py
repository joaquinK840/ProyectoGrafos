from pydantic import Basemodel

class UserPayload(Basemodel):
    name:str