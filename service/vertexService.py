from repository.vertexRepository import get_airports, get_airportById

def getAllAirports()-> dict:
    return get_airports()

def getAirportById(IATA:str)-> dict:
    return getAirportById(IATA)