from fastapi import APIRouter,HTTPException
from service.vertexService import getAllAirports,getAirportById

router = APIRouter()

@router.get("/airports")
def get_airports():
    return getAllAirports()

@router.get("/airports/{IATA}")
def get_airport(IATA:str):
    try:
        return getAirportById(IATA.upper())
    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e))
